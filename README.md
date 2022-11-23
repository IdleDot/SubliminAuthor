# SubliminAuthor

This is a program designed to turn audio files with commands or affirmations into an overwhelming binaural multi-layered wall of sound.

How to use:

When the interface pops up, click on "Browse" next to "Input files" and select the audio files of your commands. Note that this ONLY works as intended with mono 16-bit wav files with 44.1kHz sample rate. You can check this by going to your desired file in file explorer, right-clicking, selecting "Properties", heading to the "Details" tab, and scrolling down to "Bit rate". If it says 705 kbps then you should be ok, if not you should be able to do a quick conversion with Audacity. Once the files are selected, you should see them listed in the bottom half of the window. (Edit: In order to randomise the files, each command must be a separate audio file.)

Next, click on "Browse" next to "Output folder" and select a folder where you want the result to be saved. When done, this should also be visible in the bottom half of the window. You must also type a name for the output file in the "Output File Name" field.

Here's what the settings do:

Track density - How many layers of audio you wish to have. I was using 10 for tests and it worked fine. You can have as many as you want in theory, but a higher number will result in longer render times, and anything too high will make it not finish rendering due to a memory error. The setting must be a number 1 or higher and not a decimal.

Length (minutes) - How long you want the output to be in minutes. Pretty self-explanatory. The same rules apply as track density: the longer you make it the longer it'll take, and too long will result in a memory error. I believe the limit for memory errors is when Track density * Length > 1500 (resulting in over 8GB of memory required) but I haven't tested this in detail. Must be a number higher than 0, but can be decimal.

Pan movement - Check this box if you want the audio tracks to shuffle around the L/R space. This was result in ~65% longer render times, but will make the output sound busier (but honestly you don't need it, and I usually left it off while testing).

Seconds per Pan Movement - The rate at which the audio tracks shuffle around. Note that the change is gradual and they're always moving, but this rate is how often they reach their random destination and generate a new one to go to. This is irrelevant if Pan Movement is off, but it still needs to be a number higher than 0 (can be a decimal) or else the render won't work, even when Pan Movement is off.

Brainwash Me (aka export): When you set your settings and click this, your file should start exporting. This will take a while - AT LEAST the same amount of time as the file length, so be patient. (Edit: Also, be sure to keep the window open while rendering! If you close the window it will abort the rendering process.)

The progress works as follows:

"x of (Track Density) tracks generated"

"x of (Length in seconds) seconds rendered"

"normalising file"

"Done"

Don't click "Brainwash me" again until you see "Done".

Just as a sidenote: I couldn't figure out how to make error messages pop up in the interface whenever Python's terminal gives them, so if you did something wrong it won't tell you. If it's stuck on one progress phase for a suspiciously long time, you might have to close and reopen the program and try again. That said, sometimes the status display also lags for a long time, so uh... you'll have to make your own judgement there until I fix it. Sorry. :/

I think that's everything. I'm very new to coding so sorry if I made it overly cumbersome, but hopefully it does what it's supposed to do on your end too. Comment or DM me if you're having issues with it. Feedback on how to improve the code is welcome but please be nice about it because my self-esteem is very fragile and I worked very hard on this.

Don't be predatory with stuff you make with this program or it'll make me sad.

Happy trancing, everyone.
