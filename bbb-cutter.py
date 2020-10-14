#!/usr/bin/python3.6
import shutil
import sys
import xml.etree.ElementTree as etree
import os
import csv
import re
from datetime import datetime

# Get seconds from MM:SS
def getSec(time_str):
    try:
	    m, s = time_str.split(':')
	    return int(m) * 60 + int(s)
    except ValueError:
	    return None

# Copy directory tree
def copyTree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def trimVideo(src_path, dst_path, video_path, offset_start, offset_end):

    src_file = src_path+video_path

    [video_dir, video_file] = video_path.strip('/').split('/')

    if os.path.isfile(src_file):
	    os.mkdir(dst_path+"/"+video_dir)

	    # here video processing
	    try:
		    stream = ffmpeg.input(src_file)
		    vid = (
			    stream.video
			    .trim(start=offset_start, end=offset_end)
			    .setpts ('PTS-STARTPTS')
		    )
		    aud = (
			    stream.audio
			    .filter_('atrim', start = offset_start, end = offset_end)
			    .filter_('asetpts', 'PTS-STARTPTS')
		    )
		    p = ffmpeg.probe(src_file, select_streams='a'); # checking if it has audio
		    if p['streams']:
			    joined = ffmpeg.concat(vid, aud, v=1, a=1)
			    output = ffmpeg.output(joined, dst_path+video_path)
		    else:
			    output = ffmpeg.output(vid, dst_path+video_path)

#			output = ffmpeg.output(joined, "test.webm", c="copy")
#			output = ffmpeg.output(joined, new_meeting_id+".webm")


		    output.run()

	    except AttributeError:
		    print("You have to install ffmpeg-python module instead of ffmpeg.")
		    sys.exit(-1)
    else:
	    print("Warning! No video file: "+src_file)
    return

def processMetadata(src_path, dst_path, new_meeting_id, new_name, new_start_time, new_duration):
    metadataXML = src_path + "/metadata.xml"
    if not os.path.exists(metadataXML):
	    print("Warning! Wrong metafile path: {}".format(metadataXML))
    else:
	    tree = etree.parse(metadataXML)
	    root = tree.getroot()
	    id = root.find("id")
	    old_meeting_id = id.text
	    id.text = new_meeting_id

	    start_time = root.find("start_time")
	    new_start_time = int(start_time.text) + new_start_time * 1000
	    new_duration = new_duration * 1000
	    new_end_time = new_start_time + new_duration

	    start_time.text = str(new_start_time)

	    end_time = root.find("end_time")
	    end_time.text = str(new_end_time)

	    playback = root.find("playback")
	    meeting = root.find("meeting")
	    meeting.set("id", new_meeting_id)
	    meeting.set("name", new_name)
#	    meeting.set('external_id', )

	    size = playback.find("size")
	    size.text = "31337" # need to calculate real size in future

	    meetingName = root.find("meta").find("meetingName")
	    meetingName.text = new_name
	    duration = playback.find("duration")
	    duration.text = str(new_duration)

	    link = playback.find("link")
	    link.text = link.text.replace("playback.html?meetingId="+old_meeting_id, "playback.html?meetingId="+new_meeting_id)
#	    txtLink = link.text
#	    link.text = re.sub(r'playback.html\?meetingId\=.+',
#				'playback.html?meetingId='+new_meeting_id,
#				 txtLink)

	    tree.write(dst_path+"/metadata.xml", xml_declaration=True, encoding="UTF-8")
    return new_start_time, new_end_time

def processEvents(src_path, dst_path, events_file, offset_start, offset_end=0):
    eventsXML = src_path + events_file
    if not os.path.exists(eventsXML):
	    print("Warning! Wrong events path: {}".format(eventsXML))
    else:
	    tree = etree.parse(eventsXML)
	    root = tree.getroot()
	    events = root.findall("event")
	    for event in events:
		    ts = event.get("timestamp")
		    if ts:
			    ts = float(ts)
			    if ts<offset_start or ts>offset_end:
				    root.remove(event) # out of our range
			    else:
				    event.set("timestamp", str(round(ts - offset_start, 1)))
		    start_ts = event.get("start_timestamp")
		    stop_ts = event.get("stop_timestamp")
		    if start_ts and stop_ts:
			    start_ts =  float(start_ts)
			    stop_ts =  float(stop_ts)
			    if(start_ts>=offset_start and start_ts<offset_end):
				    event.set("start_timestamp", str(round(start_ts - offset_start, 1)))
				    if(stop_ts<offset_end):
					    event.set("stop_timestamp", str(round(stop_ts - offset_start, 1)))
				    else:
					    event.set("stop_timestamp", str(offset_end))
			    else:
				    root.remove(event) # out of our range

	    tree.write(dst_path+events_file, xml_declaration=True, encoding="UTF-8")
    return

def processSlides(src_path, dst_path, slides_file, offset_start, offset_end=0):
    slidesXML = src_path + slides_file
    if not os.path.exists(slidesXML):
	    print("Warning! Wrong slides path: {}".format(eventsXML))
    else:
	    tree = etree.parse(slidesXML)
	    root = tree.getroot()
	    chattimelines = root.findall("chattimeline")
	    for ctl in chattimelines:
		    ts = ctl.get("in")
		    if ts:
			    ts = float(ts)
			    if ts<offset_start or ts>offset_end:
				    root.remove(ctl) # out of our range
			    else:
				    ctl.set("in", str(round(ts - offset_start)))

	    tree.write(dst_path+slides_file, xml_declaration=True, encoding="UTF-8")
    return

def processShapes(src_path, dst_path, shapes_file, offset_start, offset_end=0):
    shapesXML = src_path + shapes_file
    if not os.path.exists(shapesXML):
	    print("Warning! Wrong shapes path: {}".format(shapesXML))
    else:
	    etree.register_namespace("", "http://www.w3.org/2000/svg")
	    tree = etree.parse(shapesXML)
	    root = tree.getroot()
	    images = root.findall("image")
	    for img in images:
		    start_ts = img.get("in")
		    stop_ts = img.get("out")
		    if start_ts and stop_ts:
			    start_ts =  float(start_ts)
			    stop_ts =  float(stop_ts)
			    if(start_ts>=offset_start and start_ts<offset_end):
				    img.set("in", str(round(start_ts - offset_start, 1)))
				    if(stop_ts<offset_end):
					    img.set("out", str(round(stop_ts - offset_start, 1)))
				    else:
					    img.set("out", str(offset_end))
			    else:
				    root.remove(img) # out of our range

	    with open(dst_path+shapes_file, 'wb') as f:
		    f.write('<?xml version="1.0"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'.encode('utf8'))
		    f.write(etree.tostring(root, encoding="UTF-8"))
    return


try:
    import ffmpeg
except ImportError:
    print("No ffmpeg-python module installed. You have to run 'pip3 install ffmpeg-python' before run this.")
    sys.exit(-1)

if len(sys.argv)<3:
    print("Required parameter missing!")
else:
    if not os.path.isfile(sys.argv[3]):
	    print("No CSV file found")
	    sys.exit(-1)

    print("Processing...")
    with open(sys.argv[3], newline='') as csvfile:
	    reader = csv.reader(csvfile, delimiter=';', quotechar='|')
	    hdr = next(reader)

	    dst_base = sys.argv[2].rstrip('/')
	    try:
		    hdr.index("event_id")
		    reportTSV = open(dst_base+"/report.txt", 'wt')
		    reportTSV.write("event_id\tplayback_id\tplayback_start\tplayback_duration\n")
		    reportTSV.close()
	    except:
		    'no report'

	    for row in reader:
		    offset_start = getSec(row[hdr.index("offset_start")])
		    offset_end = getSec(row[hdr.index("offset_end")])
		    if offset_start is None or offset_end is None:
#			    print("Row with subject '{}' is skipped because of incorrect start and end times.".format(row[hdr.index("subject")]))
			    "rem"
		    else:
			    old_meeting_id = row[hdr.index("meeting_id")]
			    src_base = sys.argv[1].rstrip('/')
#			    dst_base = "./presentation/"
			    src_path = src_base+'/'+old_meeting_id

			    duration = offset_end - offset_start
			    if row[hdr.index("lastname")]!="NULL" and row[hdr.index("firstname")]!="NULL":
				    new_meeting_id = row[hdr.index("firstname")]+" "+row[hdr.index("lastname")]
			    else:
				    new_meeting_id = row[hdr.index("author")]

			    new_meeting_name = new_meeting_id+'. '+row[hdr.index("subject")]+" ("+row[hdr.index("hall")]+")" # TODO: check existance of the each index
			    new_meeting_id = "speaker-"+"".join(new_meeting_id.split()) # replace all white spaces

			    dst_path = dst_base+"/"+new_meeting_id
			    cnt = 2
			    proposal_meeting_id = new_meeting_id
			    while os.path.exists(dst_base+'/'+proposal_meeting_id): # trying to make unique ids
				    proposal_meeting_id = new_meeting_id+str(cnt)
				    cnt += 1

			    new_meeting_id = proposal_meeting_id
			    dst_path = dst_base+'/'+new_meeting_id

			    os.makedirs(dst_path)
			    os.mkdir(dst_path+"/presentation")
			    copyTree(src_path+"/presentation", dst_path+"/presentation")

			    shutil.copy2(src_path+"/captions.json", dst_path)
			    shutil.copy2(src_path+"/presentation_text.json", dst_path)

			    new_start_time, new_end_time = processMetadata(src_path, dst_path, new_meeting_id, new_meeting_id, offset_start, duration)

			    processEvents(src_path, dst_path, "/cursor.xml", offset_start, offset_end)
			    processEvents(src_path, dst_path, "/panzooms.xml", offset_start, offset_end)
			    processEvents(src_path, dst_path, "/deskshare.xml", offset_start, offset_end)
			    processSlides(src_path, dst_path, "/slides_new.xml", offset_start, offset_end)
			    processShapes(src_path, dst_path, "/shapes.svg", offset_start, offset_end)

			    try:
				    hdr.index("event_id")
				    reportTSV = open("report.txt", 'at+')
				    reportTSV.write("{}\t{}\t{}\t{}\n".format(row[hdr.index("event_id")], new_meeting_id, new_start_time, duration*1000))
				    reportTSV.close()
			    except:
				    'handle somehow'

			    trimVideo(src_path, dst_path, "/video/webcams.webm", offset_start, offset_end)
			    trimVideo(src_path, dst_path, "/deskshare/deskshare.webm", offset_start, offset_end)
