"C:\Program Files\7-Zip\7z.exe" a -r  repo/plugin.video.relict.sovok.tv/plugin.video.relict.sovok.tv-%1.zip plugin.video.relict.sovok.tv/*  -x!.idea -x!*.iml -x!*.pyo
cp plugin.video.relict.sovok.tv/changelog.txt repo/plugin.video.relict.sovok.tv/changelog-%1.txt
python2.7 addons_xml_generator.py 