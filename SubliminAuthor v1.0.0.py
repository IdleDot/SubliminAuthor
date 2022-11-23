selected_output_folder = ""
sublim_input_files = []
sublim_pan_swirl = False

import math
import random
import os

seed_list = []
seed_list_l = []
seed_list_r = []

def four_byte(x):
    #convert integer file size to a four byte sequence for new file to read
    return bytearray([math.trunc(x) % 256, math.trunc(x/256) % 256, math.trunc(x/(256**2)) % 256, math.trunc(x/(256**3))])

def append_files(output_folder, file_list, file_name_new):
    file_list_bytes = []
    file_list_sizes = []

    new_file = open(output_folder + file_name_new + ".wav", 'wb')

    #open files and note their sizess (based on bytes 5-8 of each files)
    for i in range(0,len(file_list)):
        file_list_bytes.append(open(file_list[i], 'rb').read())
        file_list_sizes.append(file_list_bytes[i][7]*(256**3) + file_list_bytes[i][6]*(256**2) + file_list_bytes[i][5]*256 + file_list_bytes[i][4] + 8)

    file_size_total = sum(file_list_sizes)
    
    #write new header with summed file size to new file ("RIFF" + file size minus 8 + some other text + file size minus 44)
    new_file.write(bytearray([82,73,70,70]) + four_byte(file_size_total - 8) + bytearray([87,65,86,69,102,109,116,32,16,0,0,0,1,0,1,0,68,172,0,0,136,88,1,0,2,0,16,0,100,97,116,97]) + four_byte(file_size_total - 44))

    #write each of the input files (minus their headers) to new file
    for i in range(0,len(file_list_bytes)):
        new_file.write(file_list_bytes[i][44:])

def generate_pan_seeds(tracks, time_points):    
    for _ in range (0,tracks + 600):
        seed_list.append([])
        seed_list_l.append([])
        seed_list_r.append([])
    
    for _ in range(0,int(time_points+1)):
        #create empty lists
        values = []
        random_values = []

        #values has numbers in order
        for i in range(0,tracks+1):
            values.append(i)

        #pick a random item from values, add it to random values, then delete from values until values is empty
        while len(values) > 1:
            random_var = random.randrange(0,len(values))
            random_values.append(values[random_var])
            del values[random_var]
        random_values.append(values[0])
        del values[0]

        #add one of each random values to each seed in seed list
        for j in range(0,tracks+1):
            seed_list[j].append((random_values[j]) / tracks)
        
    for i in range(0,tracks+1):
        for j in seed_list[i]:
            if(j > 0.5):
                seed_list_l[i].append(round((1-j)*2,5))
            else:
                seed_list_l[i].append(1.0)
        for _ in range(0,1000):
            seed_list_l[i].append(seed_list_l[i][-1])

    for i in range(0,tracks+1):
        for j in seed_list[i]:
            if(j < 0.5):
                seed_list_r[i].append(round(j*2,5))
            else:
                seed_list_r[i].append(1.0)    
        for _ in range(0,1000):
            seed_list_r[i].append(seed_list_r[i][-1])

def merge_tracks(output_folder, file_list, seconds_per_change_rate, pan_swirl, file_name_new):
    samples_per_change_rate = seconds_per_change_rate * 44100
    file_list_bytes = []
    file_list_sizes = []

    #open files
    for i in range(0,len(file_list)):
        file_list_bytes.append(open(output_folder + file_list[i] + ".wav", 'rb').read())
        file_list_sizes.append(len(file_list_bytes[i]))
    new_file = open(output_folder + file_name_new + ".wav", 'wb')

    #take new header from longest file
    file_size_final = max(file_list_sizes) * 2

    #construct new header with summed file size ("RIFF" + file size minus 8 + some other text + file size minus 44)
    new_header = bytearray([82,73,70,70]) + four_byte(file_size_final - 8) + bytearray([87,65,86,69,102,109,116,32,16,0,0,0,1,0,2,0,68,172,0,0,16,177,2,0,4,0,16,0,100,97,116,97]) + four_byte(file_size_final - 44)
    new_file.write(new_header)

    #remove old headers from files
    for i in range(0, len(file_list_bytes)):
        file_list_bytes[i] = file_list_bytes[i][44:]

    #split into 1-sample chunks, write each individually
    for a in range(0,int((file_size_final - 44) / 4)):
        summed_bytes = []
        summed_bytes_l = []
        summed_bytes_r = []

        #convert 2-byte chunks to integers
        for i in range(0,len(file_list_bytes)):
            if a*2+1 > len(file_list_bytes[i]):
                summed_bytes.append(0)
            else:
                summed_bytes.append((((256 * file_list_bytes[i][a*2+1] + file_list_bytes[i][a*2]) + 32768) % 65536) - 32768)

        #randomise volume based on pan seeds
        if pan_swirl == True:
            for i in range(0,len(summed_bytes)):
                index = int(math.trunc(a/samples_per_change_rate))
                prev_seed_value = seed_list_l[i][index]
                next_seed_value = seed_list_l[i][index+1]
                summed_bytes_l.append(int(summed_bytes[i] * (prev_seed_value + (next_seed_value-prev_seed_value)/samples_per_change_rate * (a % samples_per_change_rate))))

                index = int(math.trunc(a/samples_per_change_rate))
                prev_seed_value = seed_list_r[i][index]
                next_seed_value = seed_list_r[i][index+1]
                summed_bytes_r.append(int(summed_bytes[i] * (prev_seed_value + (next_seed_value-prev_seed_value)/samples_per_change_rate * (a % samples_per_change_rate))))
        else:
            for i in range(0,len(summed_bytes)):
                summed_bytes_l.append(int(summed_bytes[i] * seed_list_l[i][0]))
                summed_bytes_r.append(int(summed_bytes[i] * seed_list_r[i][0]))

        #add values from lists
        layered_sample_l = int(sum(summed_bytes_l) / len(file_list))
        layered_sample_r = int(sum(summed_bytes_r) / len(file_list))

        #convert integers back into bytes
        split_bytes = []
        if layered_sample_l < 0:
            split_bytes.append(layered_sample_l % 256)
            split_bytes.append(math.trunc(layered_sample_l/256) + 255)
        else:
            split_bytes.append(layered_sample_l % 256)
            split_bytes.append(math.trunc(layered_sample_l/256))

        if layered_sample_r < 0:
            split_bytes.append(layered_sample_r % 256)
            split_bytes.append(math.trunc(layered_sample_r/256) + 255)
        else:
            split_bytes.append(layered_sample_r % 256)
            split_bytes.append(math.trunc(layered_sample_r/256))
        split_bytes = bytearray(split_bytes)

        #write to new file
        new_file.write(split_bytes)

        if (a+1) % 44100 == 0:
            print_message(str(math.trunc((a+1)/44100)) + " of " + str(math.trunc(((file_size_final - 44) / 4)/44100)) + " seconds rendered")

def normalise_file(output_folder,input_file,output_file):
    file_a =  open(output_folder + input_file + ".wav", 'rb').read()

    header = file_a[:44]
    file_a = file_a[44:]

    summed_bytes = []
    for x, y in zip(file_a[0::2],file_a[1::2]):
        summed_bytes.append((((256 * y + x) + 32768) % 65536) - 32768)

    amplification_factor = 32768 / abs(max(summed_bytes)) * 0.99

    amplified_bytes = []
    for i in range(0,len(summed_bytes)):
        amplified_bytes.append(int(summed_bytes[i] * amplification_factor))

    split_bytes = []
    for i in amplified_bytes:
        if i < 0:
            split_bytes.append(i % 256)
            split_bytes.append(math.trunc(i/256) + 255)
        else:
            split_bytes.append(i % 256)
            split_bytes.append(math.trunc(i/256))
    split_bytes = bytearray(split_bytes)

    new_file = open(output_folder + output_file + ".wav", 'wb')
    new_file.write(header + split_bytes)

def commence_brainwashing():
    message_selected_files = tk.Label(root, text=(chr(10) + " "*1000)*1000)
    message_selected_files.grid(column=0,row=4,columnspan=9, sticky=tk.NW)
    message_selected_output_folder = tk.Label(root, text=(chr(10) + " "*1000)*1000)
    message_selected_output_folder.grid(column=0,row=3,columnspan=9, sticky=tk.NW)
    brainwash_me(selected_output_folder + "/",sublim_input_files,output_file_entry.get(),int(length_entry.get()),int(track_density_entry.get()),int(seconds_per_change_rate_entry.get()),sublim_pan_swirl)

def print_message(print_text):
    current_status = tk.Label(root, text=print_text)
    current_status.grid(column=0,row=3,columnspan=9, sticky=tk.NW)
    current_status.wait_visibility()

def clear_print_message():
    current_status = tk.Label(root, text=(chr(10) + " "*1000)*1000)
    current_status.grid(column=0,row=3,columnspan=9, sticky=tk.NW)
    current_status.wait_visibility()

def brainwash_me(output_folder,input_files,output_file,length,track_density,seconds_per_change_rate, pan_swirl):
    #get lengths of all files
    file_length_list = []
    for i in input_files:
        looking_at_file_for_length = open(i, 'rb').read()
        file_length_list.append(looking_at_file_for_length[7]*(256**3) + looking_at_file_for_length[6]*(256**2) + looking_at_file_for_length[5]*256 + looking_at_file_for_length[4] - 36)

    clear_print_message()

    #for every required track, generate a random list of files from input_files until it's long enough, then append into one audio file
    print_message("0 of " + str(track_density) + " tracks generated")
    for i in range(1,track_density+1):
        track_content_list = []
        track_length = 0
        while track_length < (length * 2 * 60 * 44100):
            randomiser = random.randrange(0,len(input_files))
            track_content_list.append(input_files[randomiser])
            track_length = track_length + file_length_list[randomiser]
        append_files(output_folder,track_content_list,"sublim_track_" + str(i))
        print_message(str(i) + " of " + str(track_density) + " tracks generated")

    generate_pan_seeds(track_density, length * 60 / seconds_per_change_rate)

    #get a list of the tracks we just generated to put them into the function
    file_layer_list = []
    for i in range(1,track_density+1):
        file_layer_list.append("sublim_track_" + str(i))
    clear_print_message()
    merge_tracks(output_folder,file_layer_list,seconds_per_change_rate,pan_swirl,"sublim_track_quiet")

    clear_print_message()
    print_message("normalising file")
    normalise_file(output_folder,"sublim_track_quiet",output_file)

    for i in range(1,track_density+1):
        os.remove(output_folder + "sublim_track_" + str(i) + ".wav")
    os.remove(output_folder + "sublim_track_quiet.wav")

    clear_print_message()
    print_message("Done")

#setting up the GUI
import tkinter as tk
from tkinter import ttk, filedialog

selected_files  = []
selected_output_folder = str("")

root = tk.Tk()
root.title("New Program")
root.geometry("506x506+50+50")
root.title("SubliminAuthor v1.0 by Drew Ellison")
root.columnconfigure(0,weight=1)
root.columnconfigure(1,weight=1)
root.columnconfigure(2,weight=1)
root.columnconfigure(3,weight=1)
root.columnconfigure(4,weight=1)
root.columnconfigure(5,weight=1)
root.columnconfigure(8,weight=300)

#"Input files" text and browse button
message1 = tk.Label(root, text="Input files:")
message1.grid(column=4,row=0,sticky=tk.W,padx=(10,0))

def open_file():
    global sublim_input_files
    sublim_input_files = filedialog.askopenfilenames(filetypes=[('wav files', '*.wav')])
    message_selected_files = tk.Label(root, text=(chr(10) + " "*1000) *1000)
    message_selected_files.grid(column=0,row=4,columnspan=9, sticky=tk.NW)
    vertical_list = []
    vertical_list = ["Input files:"]
    for x in range(0,len(sublim_input_files)):
        vertical_list.append(chr(10))
        vertical_list.append(sublim_input_files[x])
    message_selected_files = tk.Label(root, text=vertical_list)
    message_selected_files.grid(column=0,row=4,columnspan=9, sticky=tk.NW)

button_browse = ttk.Button(root, text='Browse...', width=10, command=open_file)
button_browse.grid(column=5,row=0, sticky=tk.W)

#"Output folder" text and browse button
message2 = tk.Label(root, text="Output folder:")
message2.grid(column=4,row=1,sticky=tk.W,padx=(10,0))

def select_output_folder():
    global selected_output_folder
    selected_output_folder = filedialog.askdirectory()
    message_selected_output_folder = tk.Label(root, text="Output folder: " + selected_output_folder)
    message_selected_output_folder.grid(column=0,row=3,columnspan=9, sticky=tk.NW)

button_output = ttk.Button(root, text='Browse...', width=10, command=select_output_folder)
button_output.grid(column=5,row=1,sticky=tk.W)


#Track Density field
message3 = tk.Label(root, text="Track Density: ")
message3.grid(column=0,row=0,sticky=tk.W)
track_density_entry = ttk.Entry(root,width=5)
track_density_entry.grid(column=1,row=0,sticky=tk.W)

#Length field
message4 = tk.Label(root, text="Length (minutes):")
message4.grid(column=0,row=1,sticky=tk.W)
length_entry = ttk.Entry(root,width=5)
length_entry.grid(column=1,row=1,sticky=tk.W)

#Pan Movement checkbox
message5 = tk.Label(root, text="Pan Movement:")
message5.grid(column=2,row=0,sticky=tk.W,padx=(10,0))
pan_movement_checkbox = ttk.Checkbutton(root,variable=sublim_pan_swirl,onvalue=True,offvalue=False)
pan_movement_checkbox.grid(column=3,row=0,sticky=tk.W)

#Seconds per Pan Movement field
message6 = tk.Label(root, text="Seconds per Pan Movement: ")
message6.grid(column=2,row=1,sticky=tk.W,padx=(10,0))
seconds_per_change_rate_entry = ttk.Entry(root,width=5)
seconds_per_change_rate_entry.grid(column=3,row=1,sticky=tk.W)

#Output File Name field
message7 = tk.Label(root,text="Output File Name: ")
message7.grid(column=0,row=2, sticky=tk.W)
output_file_entry = ttk.Entry(root,width=39)
output_file_entry.grid(column=1,row=2,columnspan=5,sticky=tk.W)

#Brainwash Button
brainwash_button = ttk.Button(root,text="Brainwash Me!",width=24,command=commence_brainwashing)
brainwash_button.grid(column=4,row=2,columnspan=2,padx=(10,0),sticky=tk.W)

root.mainloop()