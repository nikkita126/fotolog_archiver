#!/usr/bin/env python
######################################################################
#
# getfotolog.py  1.9
#
# Python script to crawl your fotolog pages. Tested with Python 2.3
# and 2.4.
#
# author: will luo, photo (a t) wluo dot org
#
# This software is released under the MFJ Software License:
#
#   http://www.motherfuckingjackson.com/license.html
#
######################################################################
#   Modificaciones:
#   - conexion establecida usando la libreria requests
#
#





import httplib, urlparse
import requests
import os, sys, time


# define some constants
HOST = 'www.fotolog.com'    # where to get the pages from
IMGHOST = None              # image host
GBHOST = None               # guestbook host


# globals
gconn = None     # page HTTPConnection
ggbconn = None   # guest book HTTPConnection
gimgconn = None  # image HTTPConnection

# their cookie
# typically we get something like this:
#
# Set-Cookie: FCED=iF0NJuzEtixYiDg0lyXVX2IyV%2Bjt8d3xRMDJ1JJl1woDIh14JbysdJ%2BNNXHF8ZY2Y0XmVaYMiS8Kkq%2F%2Ba2bjpyqg5SDcAMA%2Fxi0gLrMyHofL; expires=Wednesday, 15-Jan-20 05:00:00 GMT; path=/; domain=.fotolog.net
#
fced = None


STYLE_BLOCK = None # style from the main page


class FatalError(Exception):
    pass


# print an error message and raise an error and exit
def raise_error(msg, ex):
    print >> sys.stderr, msg
    raise ex


def re_replace(pat, data, replacement=None):
    while True:
        m = pat.search(data)
        if m is None:
            break
        if replacement is not None:
            data = data[:m.start()] + replacement + data[m.end():]
        else:
            data = data[:m.start()] + data[m.end():]
    return data


def get_style_block(html):
    s = html.find('<style')
    e = html.find('</style>', s+1)
    e = html.find('</style>', e+1)
    return html[s:e+8] + '\n'


def reset_HTTPConnection(conn):
    '''
    reopen HTTPConnection
    '''
    conn.close()
    conn.connect()


def get_response(conn, path):
    '''
    patiently wait for our response from the HTTPConnection conn.
    path is the URL minus the protocol and host name
    
    '''
    global fced
    conn_reset = False  # did we have to reset our HTTPConnection?
    while True:
        try:
            #headers = {"USER-AGENT" : "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.10) Gecko/20050716 Firefox/1.0.6"}
            #if (fced != None):
            #    headers['Cookie'] = fced
            #print 'fetching http://%s/%s' % (conn.host, path)
            #conn.request('GET', path, '', headers)
            #r = conn.getresponse()
            #cookie = r.getheader('set-cookie', None)
            #if (cookie != None):
            #    idx = cookie.find('FCED');
            #    idx1 = cookie.find(';', idx+1)
            #    fced = cookie[idx:idx1]
            aLink = 'http://%s%s' % (HOST,path)

            r = requests.get(aLink)

            return r
        except httplib.ResponseNotReady, ex:
            print 'httplib.ResponseNotReady. retrying...'
            reset_HTTPConnection(conn)
            conn_reset = True
            continue
        except httplib.CannotSendRequest, ex:
            print 'httplib.CannotSendRequest. retrying...'
            reset_HTTPConnection(conn)
            conn_reset = True
            continue
        except Exception, ex:
            print 'ex:' + str(ex)   # keep going
            print 'ex.args:' + str(ex.args) + ', len=' + str(len(ex.args))
            if (len(ex.args) > 0) and (ex.args[0] == 10060):
                continue    # timed out
            elif not conn_reset:
                print >> sys.stdout, 'establishing a new connection'
                reset_HTTPConnection(conn)
                conn_reset = True
                continue
            else:
                raise ex


#
# save data in file fname
#
def save_content(fname, data):
    f = open(fname, 'wb')
    f.write(data)
    f.close()


#
# retrieve some content at url and save it as localfile in directory
# named by the pid parameter in the request URL.
#
def save_image(fname, imgurl):
    global IMGHOST, gimgconn
    if IMGHOST is None:
        u = urlparse.urlparse(imgurl)
        IMGHOST = u[1]
    if gimgconn is None:
        gimgconn = httplib.HTTPConnection(IMGHOST)

    r = get_response(gimgconn, imgurl)
    clenhdr = r.getheader('content-length')
    clen = 0
    loopcnt = 0
    while True:
        # loop until we really get it
        if (clenhdr != None):
            print '...trying to read ' + clenhdr + ' bytes of image'
        data = r.read()
        if (len(data) >= clen):
            break;
        else:
            print '...did not get the whole content. trying again.'
            time.sleep(3.0)
            r = get_response(gimgconn, imgurl) # try again
            continue

    save_content(fname, data)



def fetch_image(data, pid):
    '''
    parse out the main image src url and fetch it. replace its
    reference in the page data with the local version
    '''
    i = data.find('<meta property="og:image" content=')
    if (i < 0):
        raise_error('Unable to find mainphoto div', 'HTML changed')

    # start after the 'nextLink' keyword
    i = data.find('<img src="', i)
    if (i < 0):
        raise_error('Unable to find main image URL', 'HTML changed')

    istart = i+10
    iend = data.find('"', istart)
    if (iend < 0):
        raise_error('Unable to extract image URL', 'HTML changed')
    imgurl = data[istart:iend]

    # save the image locally
    imgname = pid+'.jpg'
    save_image(imgname, imgurl)

    # fixed the page html to point to the local image
    return data.replace(imgurl, imgname)


# try to create a directory but ignore if it exists
def create_dir(dirname):
    try:
        os.mkdir(dirname)
    except Exception, ex:
        if ex.args[0] != 17:   # may not have saved the page and images yet
            print ex           # so keep going eventhough the page dir.
            raise ex           # already exists


def strip_sections(data, str1, str2):
    '''
    remove the sections between str1 and str2
    '''
    while True:
        s = data.find(str1)
        if s > -1:
            e = data.find(str2, s)
            if e > -1:
                data = ''.join([data[0:s], data[e+len(str2):]])
        else:
            break
    return data


def get_starturl():
    '''
    prompt the user for the start url
    '''
    starturl = raw_input('Where should I start? (URL, e.g. ' +
                         'http://www.fotolog.net/your_name/1234\n> ')
    return starturl


def clean_main_page(data):
    # remove search banner
    data = strip_sections(data, '<!-- begin hat -->','<!-- end hat -->')

    # remove google ad div above the guestbook
    data = strip_sections(data, '<div class="ad" id="googleAd', '</div>')

    data = strip_sections(data, '<ul id="mainphotolinks">', '</ul>')

    data = strip_sections(data, '<script ', '</script>')
    data = strip_sections(data, '<SCRIPT ', '</SCRIPT>')
    data = strip_sections(data, '<div id="footer">', '</div>')
    data = strip_sections(data, '<img src="http://v.fotologs.net/v.gif?', '/>')
    return data


def fix_nav_links(data, pid, div_class):
    '''
    replace the previous/next url with an url pointing to the local one.
    return data and prev or next pid.
    '''
    i = data.find('<li class="%s">' % div_class)
    if i < 0:
        raise_error('Unable to find %s link' % div_class, 'HTML changed')

    # look for the href inside the <li> block
    endi = data.find('</li>', i)
    li_block = data[i:endi+5]

    hrefi = li_block.find('<a href="')

    if hrefi < 0:
        # no nav link
        print '%s page not found' % div_class
        return data, None

    # parse out the url
    hrefend = li_block.find('">', hrefi+1)
    navurl = li_block[hrefi+9:hrefend]
    segs = navurl.split('/')
    navpid = segs[4]
    new_navurl = navpid + '.html'

    data = data.replace(navurl, new_navurl)
    return data, navpid


def main_loop(username, pid):
    '''
    the main loop. down load all images, pages and comments for user "username"
    starting at photo id "pid"
    '''
    # set up our http connection
    global gconn
    #gconn = httplib.HTTPConnection(HOST)
    #gconn.set_debuglevel(1)

    # first page is a somewhat special case. initialize everything
    # we need before going into the main loop
    path = '/%s/%s/' % (username, pid)

   # print >> sys.stdout, 'gconn: ', gconn, ' - path: ', path

    r = get_response(gconn, path)
    if r.status_code != 200:    # error
        
        raise_error('Encountered an HTTP error:%d %s' % (r.status, r.reason),
                    'HTTP error')
    data = r.text
    global STYLE_BLOCK
    STYLE_BLOCK = get_style_block(data)
    prevpid = None
    nexturl = None

    while True:
        data = clean_main_page(data)
        data = fetch_image(data, pid)
        data, prevpid = fix_nav_links(data, pid, 'previous')
        data, nextpid = fix_nav_links(data, pid, 'next')
        filename = pid+'.html'
        save_content(filename, data)

        if not nextpid:
            print "\nReached the most recent page. We\'re done!\n"
            break

        # advance pid to the next page and start all over again
        prevpid = pid
        pid = nextpid

        # give fotolog a break
        time.sleep(2.0)

        # load up the next one
        nexturl = '/%s/%s' % (username, pid)
        r = get_response(gconn, nexturl)
        if (r.status != 200):
            raise_error('error fetching next page: %s (%d %s)' %
                        (nexturl, r.status, r.reason), 'HTTP error')
        data = r.read()

    gconn.close()     # done!


def print_header():
    print >> sys.stdout, '\n<<< fotolog archiver 1.9 >>>'
    print >> sys.stdout, '     (c) 2007 will luo'
    print >> sys.stdout, '  photo (a t) wluo dot org\n'


######################################################################
#
# main
#
if __name__ == '__main__':
    print_header()

    if len(sys.argv) > 1:
        starturl = sys.argv[1]
    else:
        starturl = get_starturl()

    print >> sys.stdout, "starting from", starturl

    # get the user name from the url
    if starturl.find('/') == -1:
        raise 'Invalid URL'
    tokens = starturl.split('/')
    if len(tokens) < 5:
        raise 'The URL you entered does not look like a valid fotolog URL'

    username = tokens[3]

    create_dir(username)
    os.chdir(username)

    # get everything ready for the start of the loop. we need the ID of the
    # page to fetch. The first time through we have to parse it from the
    # URL given by the user, which is slightly different than what we'll
    # see from the "next >>" links on the pages we will fetch later.
    ids = tokens[4].split('=')
    pid = ids[-1]

    


    main_loop(username, pid)
