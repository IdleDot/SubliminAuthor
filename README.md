# SubliminAuthor

This is a program designed to turn audio files with commands or affirmations into an overwhelming binaural multi-layered wall of sound.

How to use:

When the interface pops up, click on "Import files" and select the audio files of your commands. Once the files are selected, you should see them listed in the bottom half of the window. (Edit: In order to randomise the files, each command must be a separate audio file.)

Here's what the settings do:

Track density - How many layers of audio you wish to have. I was using 10 for tests and it worked fine. You can have as many as you want in theory, but a higher number will result in longer render times, and anything too high will make it not finish rendering due to a memory error.

Length (mins) - How long you want the output to be in minutes. Pretty self-explanatory. The same rules apply as track density: the longer you make it the longer it'll take, and too long will result in a memory error. I believe the limit for memory errors is when Track density * Length > 1500 (resulting in over 8GB of memory required) but I haven't tested this in detail.

Secs/Movement (checkbox) - Check this box if you want the audio tracks to shuffle around the L/R space. This was result in ~15% longer render times, but will make the output sound busier.

Secs/Movement - The rate at which the audio tracks shuffle around. Note that the change is gradual and they're always moving, but this rate is how often they reach their random destination and generate a new one to go to. This is irrelevant if Pan Movement is off.

Brainwash Me (aka export): When you set your settings and click this, your file should start exporting. This will take a few minutes, so be patient. (Edit: Also, be sure to keep the window open while rendering! If you close the window it will abort the rendering process.)

The progress works as follows:

"x of (Number of Input Files) files converted"

"x of (Track Density) tracks generated"

"x of (Length in seconds) seconds rendered"

"x of (Length in seconds) seconds normalised"

"Done"

Feel free to report any issues to r/SubliminAuthor or send me a DM. Feedback is welcome but please be nice.

Don't be predatory with stuff you make with this program or it'll make me sad.

Happy trancing, everyone.
