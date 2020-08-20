#!/usr/bin/env python

from __future__ import print_function
import optparse
import sys
import subprocess
import time
import re
import os
import json
import multiprocessing
import socket
import random
import shutil
import hashlib

try:
    from pkg_resources import resource_filename
except ImportError as e:
    resource_filename = None


import logging
try:
    from urllib.parse import urlparse
    from urllib.parse import quote as urlquote
    from urllib.error import URLError
    from urllib.request import Request, urlopen
except ImportError:  # Python 2
    from urlparse import urlparse
    from urllib2 import quote as urlquote
    from urllib2 import URLError, Request, urlopen

# Version information for user-agent
VERSION = "6.0.0"

user_agent = 'stashcp/{0}'.format(VERSION)

main_redirector = "root://redirector.osgstorage.org"
stash_origin = "root://stash.osgconnect.net"
writeback_host = "http://stash-xrd.osgconnect.net:1094"

# Global variable for nearest cache
nearest_cache = None

# Ordered list of nearest caches
nearest_cache_list = []

# Global variable for the location of the caches.json file
caches_json_location = None

# Global variable for the name of a pre-configured cache list
cache_list_name = None

# Global variable for the location of the token to use for reading / writing
token_location = None

# Global variable to print names of cache lists
print_cache_list_names = False

TIMEOUT = 300
DIFF = TIMEOUT * 10


def to_str(strlike, encoding="latin-1", errors="backslashescape"):
    if not isinstance(strlike, str):
        if str is bytes:
            return strlike.encode(encoding, errors)
        else:
            return strlike.decode(encoding, errors)
    return strlike


def doWriteBack(source, destination, debug=False):
    """
    Do a write back to Stash using SciTokens
    
    :param str source: The location of the local file
    :param str destination: The location of the remote file, in stash:// format
    """
    start1 = int(time.time()*1000)

    scitoken_contents = getToken()
    if scitoken_contents is None:
        logging.error("Unable to find scitokens.use file")
        return 1
    
    if debug:
        output_mode = "-v"
    else:
        output_mode = "-s"

    # Check if the source file is zero-length
    statinfo = os.stat(source)
    if statinfo.st_size == 0:
        speed_time = "--speed-time 5 "
    else:
        speed_time = ""
    command = "curl %s --connect-timeout 30 %s--speed-limit 1024 -X PUT --fail --upload-file %s -H \"User-Agent: %s\" -H \"Authorization: Bearer %s\" %s%s" % (output_mode, speed_time, source, user_agent, scitoken_contents, writeback_host, destination)

    if 'http_proxy' in os.environ:
        del os.environ['http_proxy']
    
    logging.debug("curl command: %s" % command)
    curl=subprocess.Popen([command ],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (stdout, stderr) = curl.communicate()
    (stdout, stderr) = (to_str(stdout), to_str(stderr))
    curl_exit=curl.returncode
    if statinfo.st_size == 0 and curl_exit == 28:
        logging.debug("Got curl exit code 28, but that's ok for zero-length files.  This doesn't capture connection timeouts")
        curl_exit = 0
    elif curl_exit != 0:
        logging.error(stdout)
        logging.error(stderr)
        
    sitename = os.environ.setdefault("OSG_SITE_NAME", "siteNotFound")
    end1=int(time.time()*1000)
    # Send the payload
    payload = {
        'filename': source,
        'sitename': sitename,
        'timestamp': end1,
        'host': writeback_host,
        'upload_size': os.stat(source).st_size,
        'status': 'Success',
        'tries': 1,
        'start1': start1,
        'end1': end1,
        'cache': 'None',
        'writeback': 'True'
    }
    
    payload.update(parse_job_ad())

    if curl_exit != 0:
        payload['status'] = "Failure"

    es_send(payload)
    return curl_exit
    
def getToken():
    """
    Get the token / scitoken from the environment in order to read / write
    """
    # Get the scitoken content
    scitoken_file = None

    # Command line
    if token_location:
        scitoken_file = token_location
    # Environ
    if 'TOKEN' in os.environ:
        scitoken_file = os.environ['TOKEN']

    # Backwards compatibility for getting scitokens
    if not scitoken_file and "_CONDOR_CREDS" in os.environ:
        # Token wasn't specified on the command line, try the default scitokens.use
        if os.path.exists(os.path.join(os.environ["_CONDOR_CREDS"], "scitokens.use")):
            scitoken_file = os.path.join(os.environ["_CONDOR_CREDS"], "scitokens.use")
        elif os.path.exists(".condor_creds/scitokens.use"):
            scitoken_file = os.path.abspath(".condor_creds/scitokens.use")

    if not scitoken_file or not os.path.exists(scitoken_file):
        logging.info("Unable to find token file")
        return None

    # If the scitoken file is relative, then assume it's relative
    # to the _CONDOR_CREDS directory.
    if not os.path.isabs(scitoken_file) and "_CONDOR_CREDS" in os.environ:
        os.path.join(os.environ['_CONDOR_CREDS'], scitoken_file)

    # Read in the JSON
    with open(scitoken_file, 'r') as scitoken_obj:
        try:
            token_json = json.load(scitoken_obj)
            scitoken_contents = token_json['access_token']
        except ValueError as jsonfail:
            logging.info("Falling back to old style scitoken parsing")
            scitoken_obj.seek(0)
            scitoken_contents = scitoken_obj.read()

    return scitoken_contents

def doStashCpSingle(sourceFile, destination, methods, debug=False):
    """
    Perform a single copy from StashCache federation
    """

    global nearest_cache

    # Parse the source and destination with urlparse
    source_url = urlparse(sourceFile)
    dest_url = urlparse(destination)
    understoodSchemes = ["stash", "file", ""]
    if source_url.scheme not in understoodSchemes:
        logging.error("Do not understand scheme: %s", source_url.scheme)
        return 1

    if dest_url.scheme not in understoodSchemes:
        logging.error("Do not understand scheme: %s", dest_url.scheme)
        return 1

    if dest_url.scheme == "stash":
        return doWriteBack(source_url.path, dest_url.path, debug)

    if dest_url.scheme == "file":
        destination = dest_url.path

    if source_url.scheme == "stash":
        sourceFile = source_url.path

    if not sourceFile.startswith("/"):
        sourceFile = "/" + sourceFile

    sitename = os.environ.setdefault("OSG_SITE_NAME", "siteNotFound")

    # Fill out the payload as much as possible
    filename = destination + '/' + sourceFile.split('/')[-1]
    
    payload = {}
    
    payload['filename'] = sourceFile
    payload['sitename'] = sitename
    payload.update(parse_job_ad())


    # Calculate the starting time
    start1 = int(time.time()*1000)

    # Go through the download methods
    cur_method = methods[0]
    success = False
    for method in methods:
        cur_method = method
        if method == "cvmfs":
            logging.info("Trying CVMFS...")
            if download_cvmfs(sourceFile, destination, debug, payload):
                success = True
                break
        elif method == "xrootd":
            logging.info("Trying XrootD...")
            if download_xrootd(sourceFile, destination, debug, payload):
                success = True
                break
        elif method == "http":
            logging.info("Trying HTTP...")
            if download_http(sourceFile, destination, debug, payload):
                success = True
                break
        else:
            logging.error("Unknown transfer method: %s", method)

    end1 = int(time.time()*1000)
    payload['start1']=start1
    payload['end1']=end1
    payload['timestamp']=end1
    payload['download_time']=end1-start1
    if success:
        payload['status'] = 'Success'

        # Get the final size of the downloaded file
        if os.path.isdir(destination):
            destination += "/"
        dest_dir, dest_filename = os.path.split(destination)

        if dest_filename:
            final_destination = destination
        else:
            final_destination = os.path.join(dest_dir, os.path.basename(sourceFile))
        payload['filesize'] = os.stat(final_destination).st_size
        payload['download_size'] = payload['filesize']
    else:
        logging.error("All methods failed! Unable to download file.")
        payload['status'] = 'Fail'

    es_send(payload)
    return 0 if success else 1


def download_cvmfs(sourceFile, destination, debug, payload):

    # First, check if the file is available in CVMFS
    cvmfs_file = os.path.join("/cvmfs/stash.osgstorage.org", sourceFile.lstrip("/"))
    logging.debug("Checking if the CVMFS file exists: %s", cvmfs_file)
    if os.path.exists(cvmfs_file):
        try:
            shutil.copy(cvmfs_file, destination)
            logging.debug("Succesfully copied file from CVMFS!")
            end1 = int(time.time()*1000)
            payload['tries']=1
            payload['cache']="CVMFS"
            payload['host']="CVMFS"
            return True
            
        except IOError as e:
            logging.warning("Unable to copy with CVMFS, even though file exists: %s", str(e))
            return False

    else:
        logging.debug("CVMFS File does not exist")

    return False

def download_xrootd(sourceFile, destination, debug, payload):
    """
    Download from the nearest cache, if that fails, fallback to
    the stash origin.
    """
    global nearest_cache
    global nearest_cache_list

    # Check for xrootd, return quickly if it's not available
    if not check_for_xrootd():
        return False

    # If the cache is not specified by the command line, then look for the closest
    if not nearest_cache:
        nearest_cache = get_best_stashcache()
        if not nearest_cache:
            logging.error("No cache found")
            return False
    
    # Try 3 times to download from the 3 nearest caches
    num_available_caches = len(nearest_cache_list)
    tries = 0
    xrd_exit = ""
    for cache_idx in range(min(3, num_available_caches)): # try 3 caches, or how ever many caches are in the list
        tries = cache_idx+1
        cache = nearest_cache_list[cache_idx]
        logging.debug("Using Cache %s", cache)
        xrd_exit = timed_transfer(filename=sourceFile, debug=debug, cache=cache, destination=destination)
        payload['cache' + str(tries)] = cache
        payload['xrdexit' + str(tries)] = xrd_exit

        if xrd_exit=='0': # Transfer worked
            logging.debug("Transfer success using %s", cache)
            status = "Cache Success"
            break # Break out of the for loop, transfer worked!
        else:
            logging.debug("xrdcp from cache failed on %s, pulling from next nearest cache", cache)
            status = "Cache Download Failure"

    payload['status']=status
    payload['tries']=tries

    if xrd_exit == '0':
        return True
    else:
        return False

def check_for_xrootd():
    """
    Check if xrootd is installed by checking if the xrdcp command returns a reasonable output
    """
    # xrdcp output the version on stderr, what?!?
    check_command = "xrdcp -V 2>&1"
    logging.debug("Running the command to check of xrdcp existance: %s", check_command)
    command_object = subprocess.Popen([check_command], stdout=subprocess.PIPE, shell=True)
    xrdcp_version = to_str(command_object.communicate()[0])
    if command_object.returncode == 0:
        logging.debug("xrdcp version: %s", xrdcp_version)
        return xrdcp_version
    else:
        logging.debug("xrdcp command returned exit code: %i", command_object.returncode)
        return False


def download_http(source, destination, debug, payload):
    """
    Download from the nearest cache with HTTP
    """
    global nearest_cache
    global nearest_cache_list

    logging.debug("Downloading with HTTP")

    #scitoken_contents = getToken()
    scitoken_contents = None

    if not nearest_cache:
        nearest_cache = get_best_stashcache()

    # Ok, now run the curl command:
    if debug:
        output_mode = "-v"
    else:
        output_mode = "-s"

    # The command will cd into destination directory and then run curl
    if os.path.isdir(destination):
        destination += "/"
    dest_dir, dest_filename = os.path.split(destination)
    if not dest_dir:
        dest_dir = "."

    if dest_filename:
        download_output = "-o %s" % dest_filename
        final_destination = destination
    else:
        download_output = "-O"
        final_destination = os.path.join(dest_dir, os.path.basename(source))
    
    # Try 2 nearest caches
    success = False
    start = end = 0
    tried_cache = ""
    tries = 0
    # Try the 3 nearest caches
    for cache in nearest_cache_list[:min(3, len(nearest_cache_list)]:
        tries = tries + 1
        tried_cache = cache
        # Parse the nearest_cache url, make sure it uses http
        # Should really use urlparse, but python3 and python2 urlparse imports are 
        # very different
        if cache.startswith('root://'):
            cache = cache.replace('root://', 'http://')

        # Append port 8000, which is just a convention for now, not set in stone
        # Check if the cache already has a port attached to it
        parsed_url = urlparse(cache)
        if not parsed_url.port:
            cache += ":8000"
        
        if 'http_proxy' in os.environ:
            # avoid caching big files in squid
            del os.environ['http_proxy']

        # Quote the source URL, which may have weird, dangerous characters
        quoted_source = urlquote(source)
        if scitoken_contents:
            bearer_auth = "-H \"Authorization: Bearer %s\"" % (scitoken_contents)
        else:
            bearer_auth = ""
        curl_command = "curl %s -L --connect-timeout 30 --speed-limit 1024 %s --fail -H \"User-Agent: %s\" %s %s%s" % (output_mode, download_output, user_agent, bearer_auth, cache, quoted_source)
        logging.debug("About to run curl command: %s", curl_command)
        start = int(time.time()*1000)
        command_object = subprocess.Popen([curl_command], shell=True, cwd=dest_dir)
        command_object.wait()
        end = int(time.time()*1000)
        
        if command_object.returncode == 0:
            success = True
            break

    if success:
        dlSz=os.stat(final_destination).st_size
        filesize = dlSz
        status = 'Success'
        payload['download_size']=dlSz
        payload['filesize'] = filesize

    payload['host']=tried_cache
    payload['tries']=tries
    payload['cache']=tried_cache
    if success:
        return True
    else:
        return False


def parse_job_ad():
    """
    Parse the .job.ad file for the Owner (username) and ProjectName of the callee.
    """
    temp_list = {}
    try:
        if '_CONDOR_JOB_AD' in os.environ:
            filename = os.environ['_CONDOR_JOB_AD']
        elif os.path.exists(".job.ad"):
            filename = ".job.ad"
        else:
            return {}
        with open(filename) as job_file:
            for line in job_file.readlines():
                match = re.search('^\s*(Owner|ProjectName)\s=\s"(.*)"', line,  re.IGNORECASE)
                if match:
                    temp_list[match.group(1)] = match.group(2)
    except IOError as e:
        logging.error("Unable to open the .job.ad file")

    return temp_list

def dostashcpdirectory(sourceDir, destination, methods, debug=False):
    sourceItems = to_str(subprocess.Popen(["xrdfs", stash_origin, "ls", sourceDir], stdout=subprocess.PIPE).communicate()[0]).split()
    
    for remote_file in sourceItems:
        command2 = 'xrdfs ' + stash_origin + ' stat '+ remote_file + ' | grep "IsDir" | wc -l'
        isdir=to_str(subprocess.Popen([command2],stdout=subprocess.PIPE,shell=True).communicate()[0].split()[0])
        if isdir!='0':
            result = dostashcpdirectory(remote_file, destination, debug)
        else:
            result = doStashCpSingle(remote_file, destination, methods, debug)
        # Stop transfers if something fails
        if result != 0:
            return result
    return 0


def es_send(payload):
    
    # Calculate the curernt timestamp
    payload['timestamp'] = int(time.time()*1000)
    #payload['host'] = payload['cache']
    
    def _es_send(payload):
        data = payload
        data=json.dumps(data)
        try:
            url = "http://collector.atlas-ml.org:9951"
            req = Request(url, data=data.encode("utf-8"), headers={'Content-Type': 'application/json'})
            f = urlopen(req)
            f.read()
            f.close()
        except (URLError, UnicodeError) as e:
            logging.warning("Error posting to ES: %s", str(e))

    p = multiprocessing.Process(target=_es_send, name="_es_send", args=(payload,))
    p.start()
    p.join(5)
    p.terminate()
    


def timed_transfer(filename, destination, cache, debug=False, ):
    """
    Transfer the filename from the cache to the destination using xrdcp
    """
    
    
    # All these values can be found on the xrdcp man page
    os.environ.setdefault("XRD_REQUESTTIMEOUT", "30")   # How long to wait for a read request (s)
    os.environ.setdefault("XRD_CPCHUNKSIZE", "8388608") # Size of each read request (8MB)
    os.environ.setdefault("XRD_TIMEOUTRESOLUTION", "5") # How often to check the timeouts
    os.environ.setdefault("XRD_CONNECTIONWINDOW", "30") # How long to wait for the initial TCP connection
    os.environ.setdefault("XRD_CONNECTIONRETRY", "2")   # How many time should we retry the TCP connection
    os.environ.setdefault("XRD_STREAMTIMEOUT", "30")    # How long to wait for TCP activity
    
    if not filename.startswith("/"):
        filepath=cache+":1094//"+ filename
    else:
        filepath=cache+":1094/"+ filename
    if debug:
        command="xrdcp -d 2 --nopbar -f " + filepath + " " + destination
    else:
        command="xrdcp -s -f " + filepath + " " + destination
        
    filename="./"+filename.split("/")[-1]
    if os.path.isfile(filename):
        os.remove(filename)

    if debug:
        logging.debug("xrdcp command: %s", command)
        xrdcp=subprocess.Popen([command ],shell=True,stdout=subprocess.PIPE)
    else:
        xrdcp=subprocess.Popen([command ],shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    xrdcp.communicate()
    xrd_exit=xrdcp.returncode

    return str(xrd_exit)


def get_ips(name):
    ipv4s = []
    ipv6s = []
    try:
        info = socket.getaddrinfo(name, 0, 0, 0, socket.IPPROTO_TCP)
    except:
        logging.error("Unable to look up %s", name)
        return []

    for tuple in info:
        if (tuple[0] == socket.AF_INET):
            ipv4s.append(tuple[4][0])
        elif (tuple[0] == socket.AF_INET6):
            ipv6s.append(tuple[4][0])

    # randomize the order of each
    random.shuffle(ipv4s)
    random.shuffle(ipv6s)

    # always prefer IPv4
    return ipv4s + ipv6s


# Return list of cache URLs
def get_json_caches(caches_json_location):
    try:
        with open(caches_json_location, 'r') as f:
            caches_list = json.loads(f.read())
            logging.debug("Loaded caches list from %s", caches_json_location)
    except:
        logging.error("Unable to open or parse json in %s: %s", 
            caches_json_location, str(sys.exc_info()[1]))
        return None

    usable_caches = []
    for cache in caches_list:
        if 'status' in cache and cache['status'] == 0:
            continue
        if 'name' in cache:
            usable_caches.append(cache['name'])
    if len(usable_caches) == 0:
        logging.error("No cache names found in %s without zero status", caches_json_location)
        return None

    return usable_caches


# Return list of caches as root:// URLs
def get_stashservers_caches(responselines_b):

    # After the geo order of the selected server list on line zero,
    #  the rest of the response is in .cvmfswhitelist format.
    # This is done to avoid using https for every request on the
    #  wlcg-wpad servers and takes advantage of conveniently
    #  existing infrastructure.
    # The format contains the following lines:
    # 1. Creation date stamp, e.g. 20200414170005.  For debugging
    #    only.
    # 2. Expiration date stamp, e.g. E20200421170005.  cvmfs clients
    #    check this to avoid replay attacks, but for this api that
    #    is not much of a risk so it is ignored.
    # 3. "Repository" name, e.g. Nstash-servers.  cvmfs clients
    #    also check this but it is not important here.
    # 4. With cvmfs the 4th line has a repository fingerprint, but
    #    for this api it instead contains a semi-colon separated list
    #    of named server lists.  Each server list is of the form
    #    name=servers where servers is comma-separated.  Ends with
    #    "hash=-sha1" because cvmfs_server expects the hash name
    #    to be there.  e.g.
    #    xroot=stashcache.t2.ucsd.edu,sg-gftp.pace.gatech.edu;xroots=xrootd-local.unl.edu,stashcache.t2.ucsd.edu;hash=-sha1
    # 5. A two-dash separator, i.e "--"
    # 6. The sha1 hash of lines 1 through 4.
    # 7. The signature, i.e. an RSA encryption of the hash that can
    #    be decrypted by the OSG cvmfs public key.  Contains binary
    #    information so it may contain a variable number of newlines
    #    which would have caused it to have been split into multiple
    #    response "lines".

    if len(responselines_b) < 8:
        logging.error("stashservers response too short, less than 8 lines")
        return None
    hashname_b = responselines_b[4][-5:]
    if hashname_b != b"-sha1":
        logging.error("stashservers response does not have sha1 hash: %s", to_str(hashname_b))
        return None
    hashedtext_b = b'\n'.join(responselines_b[1:5]) + b'\n'
    hash_str = hashlib.sha1(hashedtext_b).hexdigest()
    if to_str(responselines_b[6]) != hash_str:
        logging.debug("stashservers hash %s does not match expected hash %s", to_str(responselines_b[6]), hash_str)
        logging.debug("hashed text:\n%s", to_str(hashedtext_b))
        logging.error("stashservers response hash does not match expected hash")
        return None

    # Call out to /usr/bin/openssl if present, in order to avoid
    #  python dependency on a crypto package.
    if not os.path.exists("/usr/bin/openssl"):
        # The signature check isn't critical to be done everywhere;
        #  any tampering will likely to be caught somewhere and
        #  investigated.  Usually openssl is present.
        logging.debug("openssl not installed, skipping signature check")
    else:
        sig = b'\n'.join(responselines_b[7:])

        # Look for the OSG cvmfs public key to verify signature
        prefix = os.environ.get("OSG_LOCATION", "/")
        osgpub = 'opensciencegrid.org.pub'
        pubkey_files = ['/etc/cvmfs/keys/opensciencegrid.org/' + osgpub,
                        os.path.join(prefix, "etc/stashcache", osgpub),
                        os.path.join(prefix, "usr/share/stashcache", osgpub)]
        if resource_filename:
            try:
                pubkey_files.append(resource_filename(__name__, osgpub))
            except IOError as ioe:
                logging.debug("Unable to retrieve caches.json using resource string, trying other locations")

        for pubkey_file in pubkey_files:
            if os.path.isfile(pubkey_file):
                break
        else:
            logging.error("Unable to find osg cvmfs key in %r", pubkey_files)
            return None
        
        cmd = "/usr/bin/openssl rsautl -verify -pubin -inkey " + pubkey_file
        logging.debug("Running %s", cmd)
        p = subprocess.Popen(cmd, shell=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p.stdin.write(sig)
        p.stdin.close()
        decryptedhash = to_str(p.stdout.read())
        p.stdout.close()
        if hash_str != decryptedhash:
            logging.debug("stashservers hash %s does not match decrypted signature %s", hash_str, decryptedhash)
            logging.error("stashservers signature does not verify")
            return None
        logging.debug("Signature matched")

    lists = to_str(responselines_b[4]).split(';')
    logging.debug("Cache lists: %s", lists)

    if print_cache_list_names:
        names = ""
        # skip hash at the end
        for l in lists[0:-1]:
            names = names + ',' + l.split('=')[0]
        # skip leading comma
        print(names[1:])
        sys.exit(0)

    if cache_list_name == None:
        caches = lists[0].split('=')[1]
    else:
        for l in lists:
            n=len(cache_list_name)+1
            if l[0:n] == cache_list_name + '=':
                caches = l[n:]
                break
    caches_list = caches.split(',')
    for i in range(len(caches_list)):
        caches_list[i] = 'root://' + caches_list[i]
    
    return caches_list


# Return best stashcache and set nearest_cache_list global
def get_best_stashcache():
    global nearest_cache_list

    # Use the geo ip service on the WLCG Web Proxy Auto Discovery machines
    geo_ip_sites = ["wlcg-wpad.cern.ch", "wlcg-wpad.fnal.gov"]
    
    # Headers for the HTTP request
    headers = {'Cache-control': 'max-age=0', 'User-Agent': user_agent }
    
    # Randomize the geo ip sites
    random.shuffle(geo_ip_sites)

    api_text = ""

    caches_list = []

    # Check if the user provided a caches json file location
    if caches_json_location:
        if not os.path.exists(caches_json_location):
            logging.error(caches_json_location + " does not exist")
            return None
        # Use geo ip api on caches in provided json file
        caches_list = get_json_caches(caches_json_location)
        caches_string = ""
        for cache in caches_list:
            parsed_url = urlparse(cache)
            caches_string = "%s,%s" % (caches_string, parsed_url.hostname)
        # Remove the first comma
        caches_string = caches_string[1:]
        api_text = "api/v1.0/geo/stashcp/" + caches_string
    else:
        # Use stashservers.dat api
        api_text = "stashservers.dat"
        if cache_list_name != None:
            api_text += "?list=" + cache_list_name

    responselines_b = []
    i = 0
    while len(responselines_b) == 0 and i < len(geo_ip_sites):
        cur_site = geo_ip_sites[i]
        headers['Host'] = cur_site
        logging.debug("Trying server site of %s", cur_site)
        for ip in get_ips(cur_site):
            final_url = "http://%s/%s" % (ip, api_text)
            logging.debug("Querying %s", final_url)
            try:
                # Make the request
                req = Request(final_url, headers=headers)
                response = urlopen(req, timeout=10)
                if response.getcode() == 200:
                    logging.debug("Got OK code 200 from %s", cur_site)
                    responsetext_b = response.read()  # type: bytes
                    responselines_b = responsetext_b.split(b'\n')
                    response.close()
                    break
                response.close()
            except URLError as e:
                logging.debug("URL error: %s", str(e))
            except Exception as e:
                logging.debug("Error: %s", str(e))
        i+=1

    order_str = ""
    if len(responselines_b) > 0:
        order_str = to_str(responselines_b[0])
        
    if order_str == "":
        if len(caches_list) == 0:
            logging.error("unable to get list of caches")
            return None
        # Unable to find a geo_ip server to use, return random choice from caches!
        nearest_cache_list = caches_list
        random.shuffle(nearest_cache_list)
        minsite = nearest_cache_list[0]
        logging.warning("Unable to use Geoip to find closest cache!  Returning random cache %s", minsite)
        logging.debug("Randomized list of nearest caches: %s", str(nearest_cache_list))
        return minsite
    else:
        # The order string should be something like:
        # 3,1,2
        ordered_list = order_str.strip().split(",")
        logging.debug("Got order %s", str(ordered_list))

        if len(caches_list) == 0:
            # Used the stashservers.dat api
            caches_list = get_stashservers_caches(responselines_b)
            if caches_list is None:
                return None

        minsite = caches_list[int(ordered_list[0])-1]

        nearest_cache_list = []
        for ordered_index in ordered_list:
            nearest_cache_list.append(caches_list[int(ordered_index)-1])
        
        logging.debug("Returning closest cache: %s", minsite)
        logging.debug("Ordered list of nearest caches: %s", str(nearest_cache_list))
        return minsite


def main():
    global nearest_cache
    global nearest_cache_list
    global caches_json_location
    global cache_list_name
    global token_location

    usage = "usage: %prog [options] source destination"
    parser = optparse.OptionParser(usage, version="stashcp %s" % VERSION)
    parser.add_option('-d', '--debug', dest='debug', action='store_true', help='debug')
    parser.add_option('-r', dest='recursive', action='store_true', help='recursively copy')
    parser.add_option('--closest', action='store_true', help="Return the closest cache and exit")
    parser.add_option('-c', '--cache', dest='cache', help="Cache to use")
    parser.add_option('-j', '--caches-json', dest='caches_json', help="A JSON file containing the list of caches",
                      default=None)
    parser.add_option('-n', '--cache-list-name', dest='cache_list_name', help="Name of pre-configured cache list to use",
                      default=None)
    parser.add_option('--list-names', dest='list_names', action='store_true', help="Return the names of pre-configured cache lists and exit (first one is default for -n)")
    parser.add_option('--methods', dest='methods', help="Comma separated list of methods to try, in order.  Default: cvmfs,xrootd,http", default="cvmfs,xrootd,http")
    parser.add_option('-t', '--token', dest='token', help="Token file to use for reading and/or writing")
    args,opts=parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                       datefmt="%Y-%m-%dT%H:%M:%S%z")
    logger = logging.getLogger()

    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    if args.list_names:
        global print_cache_list_names
        print_cache_list_names = True
        get_best_stashcache()
        # does not return

    if args.caches_json:
        caches_json_location = args.caches_json
    elif 'CACHES_JSON' in os.environ:
        caches_json_location = os.environ['CACHES_JSON']
    else:
        prefix = os.environ.get("OSG_LOCATION", "/")
        caches_file = os.path.join(prefix, "etc/stashcache/caches.json")
        if os.path.exists(caches_file):
            caches_json_location = caches_file

    cache_list_name = args.cache_list_name
    if args.closest or args.list_names:
        print(get_best_stashcache())
        sys.exit(0)

    if len(opts) != 2:
        logging.error('Source and Destination must be specified on command line')
        parser.print_help()
        sys.exit(1)
    else:
        source=opts[0]
        destination=opts[1]

    # Check for manually entered cache to use
    if 'NEAREST_CACHE' in os.environ:
        nearest_cache = os.environ['NEAREST_CACHE']
        nearest_cache_list = [nearest_cache]
    elif args.cache and len(args.cache) > 0:
        nearest_cache = args.cache
        nearest_cache_list = [args.cache]
    
    if args.token:
        token_location = args.token

    # Convert the methods
    methods = args.methods.split(',')

    if not args.recursive:
        result = doStashCpSingle(sourceFile=source, destination=destination, methods = methods, debug=args.debug)
    else:
        result = dostashcpdirectory(sourceDir = source, destination = destination, methods = methods, debug=args.debug)
    # Exit with failure
    sys.exit(result)


if __name__ == "__main__":
    main()
