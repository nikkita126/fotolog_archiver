#!/usr/bin/env python
######################################################################
#
#   Fotolog Archiver v 2.0 - Python script to crawl your fotolog pages 
#
#   * based on the original script by will luo, photo (a t) wluo dot org
#     from http://www.wluo.org/fotologarchiver/
#   
#   * modified by @nikkita126
#  
#   # tested with Python 2.7
#
#  This software is released under the MFJ Software License:
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
import shutil # para guardar las imagenes
import os, sys, time


STYLE_BLOCK = None # style from the main page


class FatalError(Exception):
    pass


# print an error message and raise an error and exit
def raise_error(msg, ex):
    print >> sys.stderr, msg
    raise ex


def get_style_block(css_group,orig_start,orig_end):
    '''
    find fotolog's stylesheets, download them to local files
    and return a modified chunk of text with fixed references 
    '''

    #print >> sys.stdout,'---------------------',css_group

    begin_at = 0
    while True:

        i = css_group.find('<link rel="stylesheet"',begin_at)

        if i<0:
            break

        istart = css_group.find('href=',i) + 6
        iend = css_group.find('"',istart)

        style_url = css_group[istart:iend]


        # print >> sys.stdout,'---------------------',style_url

        s_req = requests.get(style_url)

        if s_req.status_code == 200:

            tokens = style_url.split('styles/')
            style_name = tokens[1] # ARCHIVO.css
            tokens2=style_name.split('?') # Some css file had that character on its name and messed things up
            style_name=tokens2[0]
            s_data=s_req.text
            save_content(style_name, s_data) # save stylesheet to local file

            css_group = css_group.replace(style_url, style_name) # update chunk of text with css files

        begin_at = iend    

    return css_group


def set_style_block(data,STYLE_BLOCK):
    '''
    fix css references in the page 
    '''

    orig_start = data.find('<link rel="stylesheet"')
    orig_end = data.find('<style')

    css_group = data[orig_start:orig_end] # chunk of text with css files

    if STYLE_BLOCK == None:
        STYLE_BLOCK = get_style_block(css_group,orig_start,orig_end)       
    
    data = data.replace(css_group,STYLE_BLOCK)

    return data,STYLE_BLOCK

def save_content(fname, data):
    '''
    save text data in file fname
    '''
    f = open(fname, 'wb')
    f.write(data.encode('utf8'))
    f.close()


def save_image(fname, imgurl):
    '''
    retrieve an image at url and save it as localfile
    '''
    response = requests.get(imgurl, stream=True)
    
    with open(fname, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response

def fetch_image(data, pid):
    '''
    parse out the main image src url and fetch it. replace its
    reference in the page data with the local version
    '''
    i = data.find('<meta property="og:image" content="')


    if (i < 0):
        raise NameError('Unable to find main image URL', 'HTML changed')

    
    istart = i+35 # (35 = length of "<meta property="og:image...")
    iend = data.find('"', istart)
    if (iend < 0):
        raise NameError('Unable to extract image URL', 'HTML changed')

    imgurl = data[istart:iend]


    # save the image locally
    imgname = pid+'.jpg'
    save_image(imgname, imgurl)


    # fixed the page html to point to the local image
    return data.replace(imgurl, imgname)


def create_dir(dirname):
    '''
    try to create a directory but ignore if it exists
    '''

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
    '''
    remove chunks of code from the original html file
    that are not important
    '''


    #####################################
    ######## NON-WRAPPER
    data = strip_sections(data, '<script', '</script>')
    data = strip_sections(data, '<SCRIPT', '</SCRIPT>')
 
    data = strip_sections(data, '<noscript', '</noscript>')
    # remove fotolog ending message
    data = strip_sections(data, '<div id="ExecuteOrder66"','</div>') #OK


    data = strip_sections(data, '<div id="fb-root">', '</div>')   #OK
    data = strip_sections(data,'<div id="flyout">','</div>') #OK

    #
    # remove log in bar
    data = strip_sections(data, '<div id="logo">', '</div>') #OK
    data = strip_sections(data, '<div id="head_bar_container">', '</div>') #OK
    data = strip_sections(data, '<div id="head_bar">', '</div>')   #OK

    #######################################
    ########## WRAPPER

    ###### FOOTER
    data = strip_sections(data, '<div id="footer">', '</div>') # OK
    
    ###### CONTAINER

    #### Anchor
    data = strip_sections(data, '<a id="anchor_flog"', '</a>') # OK

    #### Top and bottom pubs
    data = strip_sections(data,'<div class="hmads','</div>')
    data = strip_sections(data,'<div class="float_right"','</div>')
    data = strip_sections(data,'<div id="bottom_pub">','</div>')
    data = strip_sections(data,'<div id="top_pub">','</div>')

    #### promoted banners
    data = strip_sections(data,'<div id="promoted_banner">','</div>')

    #### Wall Column Left

    # "heart" button
    data = strip_sections(data,'<div class="flog_flash_button button_visible">','</div>') #OK

    # share buttons
    data = strip_sections(data, '<div class="fb-like"', '</div>') #OK
    data = strip_sections(data, '<div id="flog_img_action">', '</div>') #OK

    # slider
    data = strip_sections(data,'<div id="slide_left"','</div>')
    data = strip_sections(data,'<div id="slide_right"','</div>')
    data = strip_sections(data,'<div id="slide_container"','</div>')
    data = strip_sections(data,'<div id="block_slide"','</div>')

    # "Iniciar sesion para comentar"
    data = strip_sections(data,'<div class="flog_img_comments" id="comment_form">','</div>')

    # remove share plugin holder
    data = strip_sections(data, '<div id="facebook"', '</div>') #OK
    data = strip_sections(data, '<div id="twitter"', '</div>') #OK
    data = strip_sections(data, '<div id="pin"', '</div>') #OK
    data = strip_sections(data, '<div id="share-plugin-holder">', '</div>') #OK

    #### Wall right column
    data = strip_sections(data,'<div class="wall_right_block">','</div>')
    data = strip_sections(data,'<div id="wall_right_column">','</div>')
  
    ########
    # loader
    data = strip_sections(data,'<div class="loader">','</div>')
    data = strip_sections(data,'<div class="contentWrap">','</div>')
    data = strip_sections(data,'<div class="overlay">','</div>')

    ########   
    return data


def fix_nav_links(data, pid, link_type):
    '''
    replace the previous/next url with an url pointing to the local one.
    return data and prev or next pid.
    '''

    to_concat = None
    if link_type == 'previous':
        to_concat = ''

    elif link_type == 'next':
        to_concat = ' arrow_change_photo_right'

    to_find = '<a class="arrow_change_photo%s"' % to_concat

   
    i = data.find(to_find)

    if i < 0:
        if link_type == 'next':
            navpid = None
            return data,navpid
        raise NameError('Unable to find %s link' % link_type, 'HTML changed')


    endi = data.find('</a>', i)
    class_block = data[i:endi+4]

    hrefi = class_block.find('href="')

    if hrefi < 0:
        # no nav link
        print '%s page not found' % link_type
        return data, None

    # parse out the url
    hrefend = class_block.find('">', hrefi)

    navurl = class_block[hrefi+6:hrefend] # DUDA CUANTO SUMAR
    segs = navurl.split('/') # ['http:','','www.fotolog.com','USERNAME','pageID',[extra]]
    navpid = segs[4] # page ID
    new_navurl = navpid + '.html'

    data = data.replace(navurl, new_navurl)
    return data, navpid

def remove_hidden_posts(data):

    data = data.replace('<div class="flog_img_comments is_hidden">','<div class="flog_img_comments">')
    data = strip_sections(data,'<a class="gb_show_all"','</a>')

    return data

def main_loop(username, pid,count):
    '''
    the main loop. down load all images, pages and comments for user "username"
    starting at photo id "pid"
    '''

    


    global gconn #  BORRAR
 
    STYLE_BLOCK = None
    #STYLE_BLOCK  # save css files

    prevpid = None
    nexturl = None

    while True:
        path = 'http://www.fotolog.com/%s/%s/' % (username, pid)
        
        r = requests.get(path)
        
        if r.status_code != 200:    # error
            raise NameError('Encountered an HTTP error:%d %s' % (r.status, r.reason),
                    'HTTP error')

        data = r.text # the html page

        message = 'retrieving page %s...' % count
        sys.stdout.write(message)
        

        
        data = fetch_image(data, pid) 
        data = clean_main_page(data)
        data,STYLE_BLOCK = set_style_block(data,STYLE_BLOCK)


        if data.find('<a class="gb_show_all"') > 0:
            data = remove_hidden_posts(data)


        if count > 1:
            data, prevpid = fix_nav_links(data, pid, 'previous') # fix references to previous photo
        data, nextpid = fix_nav_links(data, pid, 'next')         # fix references to next photo
        
        filename = pid+'.html'
        save_content(filename, data)

        sys.stdout.write(' done!\n')

        if not nextpid:
            print "\nReached the last page. We\'re done!\n"
            break
        else:
            # advance pid to the next page and start all over again
            prevpid = pid
            pid = nextpid

            # give fotolog a break
            time.sleep(1.0)
            count = count+1

   # gconn.close()     # done!


def print_header():
    print >> sys.stdout, '\n<<< fotolog archiver 2.0 >>>'
    print >> sys.stdout, '     v 1.9 (c) 2007 will luo'
    print >> sys.stdout, '  modified by @nikkita126\n'


def create_start_page(pid):
    text='<html><head><META http-equiv="refresh" content="0;URL=%s.html"></head></html>' % pid

    f = open('start.html', 'w')
    f.write(text.encode('utf8'))
    f.close()

######################################################################
#
# main
#
if __name__ == '__main__':
    
    starting_time = time.time()


    print_header()

    if len(sys.argv) > 1:
        starturl = sys.argv[1]
    else:
        starturl = get_starturl()

    print >> sys.stdout, "starting from", starturl

    # get the user name from the url
    if starturl.find('/') == -1:
        raise NameError('Invalid URL')
    tokens = starturl.split('/')
    if len(tokens) < 5:
        raise NameError('The URL you entered does not look like a valid fotolog URL')

    username = tokens[3]
    ## TO-DO:
    # flujo en caso de que ya exista la carpeta
    if os.path.exists(username):
        shutil.rmtree(username)
    create_dir(username)
    os.chdir(username)

    # get everything ready for the start of the loop. we need the ID of the
    # page to fetch. The first time through we have to parse it from the
    # URL given by the user, which is slightly different than what we'll
    # see from the "next >>" links on the pages we will fetch later.
    ids = tokens[4].split('=')
    start_pid = ids[-1]

    
    count=1

    main_loop(username,start_pid,count)
    create_start_page(start_pid)

    ending_time=time.time()

    print >> sys.stdout,'\nELAPSED TIME: ',ending_time - starting_time
