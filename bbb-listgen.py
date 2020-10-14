#!/usr/bin/python3.6
from os import listdir
from os.path import isdir
import sys, os
import xml.etree.ElementTree as etree
from datetime import datetime

def getRecords(wd):
    recordsArr = []
    if not os.path.isdir(wd):
	    print("Directory does not exists!")
    else:
	    for d in os.listdir(wd):
		    if not d:
			    print("Working directory is empty.")
			    break
		    else:
			    cd = wd + '/' + d
			    if os.path.isdir(cd):
				    print("Working with directory {}...".format(d))
				    metadataXML = cd + "/metadata.xml"
#				    print("Trying to open {}".format(metadataXML))
				    if not os.path.exists(metadataXML):
					    print("Warning! Wrong metafile path: {}".format(metadataXML))
				    else:
					    elem = dict()
					    tree = etree.parse(metadataXML)
					    root = tree.getroot()
					    playback = root.find("playback")
					    meeting = root.find("meeting")
					    elem["id"] = meeting.attrib["id"]
					    elem["name"] = meeting.attrib["name"]
					    elem["externalId"] = meeting.attrib["externalId"]
					    elem["participants"] = int(root.find("participants").text)
					    elem["link"]  = playback.find("link").text
					    elem["duration"]  = int(playback.find("duration").text)
					    elem["start_time"]  = int(root.find("start_time").text)
					    elem["size"]  = int(playback.find("size").text)
					    images  = playback.find("extensions").find("preview").find("images")
					    for img in images: 
						    elem["images"] = []
						    tmp = dict()
						    tmp["width"] = img.attrib["width"]
						    tmp["height"] = img.attrib["height"]
						    tmp["alt"] = img.attrib["alt"]
						    tmp["src"] = img.text
						    elem["images"].append(tmp)

					    recordsArr.append(elem)
					    del elem
    return recordsArr

def generateHTML(recordsArr):
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>BigBlueButton records list</title>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" integrity="sha384-JcKb8q3iqJ61gNV9KGb8thSsNjpSL0n8PARn9HuZOnIxN0hoP+VmmDGMN5t9UJ0Z" crossorigin="anonymous">
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.22/css/jquery.dataTables.min.css">
</head>
<body>
<div class="container">
<div class="row">
<div class="col">
<h1>BigBlueButton records list</h1>
<table id="list" class="display" style="width:100%">
<thead>
<tr>
<th>MeetingID</th>
<th>Name</th>
<th>Preview</th>
<th>Date</th>
<th>Duration</th>
<th>Participants</th>
<th>Size</th>
</tr>
</thead>
<tbody>
"""

    for record in recordsArr:
	    html += '<tr>\n'
	    html += '<td><a href="' + record["link"] + '">' + record["id"] + '</a></td>\n'
	    html += '<td>' + record["name"] + '</td>\n'
	    html += '<td>\n'
	    for img in record["images"]:
		    html += '<img src="' + img["src"] + '"><br>\n'
	    html += '</td>\n'
	    html += '<td>' + datetime.utcfromtimestamp(record["start_time"]/1000).strftime('%Y-%m-%d %H:%M:%S') + '</td>\n'
	    html += '<td>{}:{:02d}</td>\n'.format(record["duration"]//1000//60, record["duration"]//1000%60)
	    html += '<td>' + str(record["participants"]) + '</td>\n'
	    html += '<td>' + str(record["size"]) + '</td>\n'
	    html += '</tr>\n'

    html += """
</tbody>
</table>
</div>
</div>
</div>
<script type="text/javascript" src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script type="text/javascript" src="https://cdn.datatables.net/1.10.22/js/jquery.dataTables.min.js"></script>

<script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js" integrity="sha384-9/reFTGAW83EW2RDu2S0VKaIzap3H66lZH81PoYlFhbGU+6BZp6G7niu735Sk7lN" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js" integrity="sha384-B4gt1jrGC7Jh4AgTPSdUtOBvfO8shuf57BaghqFfPlYxofvL8/KUEfYiJOMMV+rV" crossorigin="anonymous"></script>

<script type="text/javascript">
    $(document).ready(function() {
        $('#list').DataTable();
    } );
</script>
</body>
</html>"""

    return html

if len(sys.argv)<2:
    print("Required parameter missing!")
else:
    print("Processing")
    arr = getRecords(sys.argv[1].rstrip('/'))

    if not arr:
	    print("Record list is empty, nothing found!")
    else:
	    html = generateHTML(arr)
	    if len(sys.argv)<3:
		    sys.stderr.write(html)
	    else:
		    f = open(sys.argv[2], "w")
		    if not f:
			    print("Failed to write into the file {}!".format(sys.argv[2]))
		    else:
			    f.write(html)
			    f.close()
			    print("Something saved in {}.".format(sys.argv[2]))

