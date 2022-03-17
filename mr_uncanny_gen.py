from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
import textwrap

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
SCALE = 0.5
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FRAME_PADDING = 60

TIME_PERSLIDE_MIN = 3
TIME_PERSLIDE_MAX = 5 #TODO: this should be the max lenght of the current music track
TIME_PERSLIDE_PERLINE = 0.5

UNCANNY_MAX = 26
CANNY_MAX = -9

FONT = "arial.ttf"
FONT_SIZE = 60
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

PATH_CWD = os.getcwd()
PATH_TEMP_IMAGES = PATH_CWD + "/temp/frames/"
PATH_TEMP_VIDS = PATH_CWD + "/temp/vids/"
PATH_AUDIOS = PATH_CWD + "/assets/audio/"
PATH_FACES = PATH_CWD + "/assets/faces/"
PATH_FONTS = PATH_CWD + "/assets/fonts/"
FONT_SIZE = int(FONT_SIZE*SCALE)
FONT = ImageFont.truetype(PATH_FONTS + FONT, FONT_SIZE)

FRAME_WIDTH = int(FRAME_WIDTH*SCALE)
FRAME_HEIGHT = int(FRAME_HEIGHT*SCALE)
FRAME_PADDING = int(FRAME_PADDING*SCALE)

# delete old temporary files before runing again
for file in os.listdir(PATH_TEMP_IMAGES):
	os.remove(PATH_TEMP_IMAGES + file)
for file in os.listdir(PATH_TEMP_VIDS):
	os.remove(PATH_TEMP_VIDS + file)

# load user text with the story script
with open("script.txt") as file:
    script = file.readlines()

uncanny_phase = 0

# for every line in the story, generate a vid with the correct phase image and music
for slide_index, slide_data in enumerate(script):

	# skip coomented lines or empty lines
	if slide_data[0] in ["#", " ", "\n"]:
		continue

	slide_phase, slide_text = slide_data.split(" ", 1)
	
	if slide_phase[0] in ["<", ">"]:
		phase_direction = slide_phase[0]
		phase_step = len(slide_phase)

		if not phase_step:
			phase_step = 1

		phase_direction = 1 if phase_direction == ">" else -1

		uncanny_phase += int(phase_step) * int(phase_direction) 
	else:		
		uncanny_phase = int(slide_phase)

	# clamp uncanny phase to valid numbers
	if uncanny_phase > UNCANNY_MAX:
		uncanny_phase = UNCANNY_MAX
	elif uncanny_phase < CANNY_MAX:
		uncanny_phase = CANNY_MAX

	# using underscore its more usefull when looking at the files in the windows explorer
	filename = str(uncanny_phase).replace("-", "_")

	print(f"{uncanny_phase}: {slide_text[:-1]}")
	print(f"filename: {filename}")

	# GENERATE A SLIDE IMAGE
	frame = Image.new('RGB', (FRAME_WIDTH, FRAME_HEIGHT), color=0)
	face = Image.open(f"{PATH_FACES}{filename}.png")
	face = face.resize((FRAME_HEIGHT - FRAME_PADDING*2, FRAME_HEIGHT - FRAME_PADDING*2))
	frame.paste(face, (FRAME_PADDING, FRAME_PADDING))

	text = slide_text
	para = textwrap.wrap(text, width=15)

	d1 = ImageDraw.Draw(frame)

	# draw text
	current_h = FRAME_HEIGHT/2
	for line in para:
	    w, h = d1.textsize(line, font=FONT)
	    d1.text(((FRAME_WIDTH/4)*3 - w/2, current_h - len(para)/2*FONT_SIZE), line, font=FONT)
	    current_h += h

	frame_abs_path = f"{PATH_TEMP_IMAGES}{slide_index}.png"
	frame.save(frame_abs_path)


	# GENERATE SLIDE VID WITH MUSIC
	duration = TIME_PERSLIDE_MIN + len(para)*TIME_PERSLIDE_PERLINE
	if duration > TIME_PERSLIDE_MAX:
		duration = TIME_PERSLIDE_MAX
	duration = int(duration)
	
	subprocess.call([
	'ffmpeg', '-loop', '1',
	'-i', frame_abs_path,
	'-i', PATH_AUDIOS + f'{filename}.mp3',
	'-c:v', 'libx264', '-t', str(duration), '-pix_fmt', 'yuv420p', '-vf', f'scale={FRAME_WIDTH}:{FRAME_HEIGHT}', PATH_TEMP_VIDS + f'{str(slide_index).zfill(6)}.mp4'
	])

# MERGE ALL INDIVIDUAL VIDS TO THE FINAL ONE
# first must create a txt file, with all vids'paths. for later use in the ffmpeg concat command
vidspaths_content = ""
for slide_vid in os.listdir(PATH_TEMP_VIDS):
	vid_path = f"file {PATH_TEMP_VIDS + slide_vid}"
	vid_path = vid_path.replace(os.sep, '/')
	vidspaths_content += vid_path + "\n"
	print(slide_vid)
with open(PATH_TEMP_VIDS + "vidspaths.txt", "w") as f:
	f.write(vidspaths_content)
	f.close()
# actuall merge
subprocess.call([
	'ffmpeg', '-f', 'concat', '-safe', "0", "-i", PATH_TEMP_VIDS + "vidspaths.txt", "-y", "-c", "copy", "out.mp4"
])
