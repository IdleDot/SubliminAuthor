selected_output_folder = ""
sublim_input_files = []

import math
import random
import os
import numpy

seed_list = numpy.array([])
seed_list_l = numpy.array([])
seed_list_r = numpy.array([])

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
    global seed_list
    global seed_list_l
    global seed_list_r

    seed_list = numpy.empty((tracks ,0))

    for i in range(0,int(time_points+1)):
        #create empty lists
        values = []
        random_values = numpy.empty([tracks ,1])

        #values has numbers in order
        for i in range(0,tracks):
            values.append(i)

        #pick a random item from values, add it to random values, then delete from values until values is empty
        for i in range (0,tracks-1):
            random_var = random.randrange(0,len(values))
            random_values[i] = values[random_var]
            del values[random_var]
        random_values[-1] = values[0]
        del values[0]

        #add one of each random values to each seed in seed list
        seed_list = numpy.append(seed_list, random_values / (tracks-1), axis=1)

    #repeat last value a bunch so later code doesn't crash
    for _ in range(0,600):
        seed_list = numpy.append(seed_list, random_values / (tracks-1), axis=1)

    #convert one pan value into two L/R values    
    seed_list_l = seed_list * -2 + 2
    seed_list_r = seed_list * 2

    #max out each at 1.0
    for i in range(0,tracks):
        for j in range(0,int(time_points+1)):
            if seed_list_l[i][j] > 1.0:
                seed_list_l[i][j] = 1.0
            if seed_list_r[i][j] > 1.0:
                seed_list_r[i][j] = 1.0

def generate_modifiers(a, i, seconds_per_change_rate):
    global modifier_list_l
    global modifier_list_r

    modifier_list_l = numpy.empty((0,0))
    modifier_list_r = numpy.empty((0,0))

    samples_per_change_rate = seconds_per_change_rate * 44100

    index = math.trunc(a/samples_per_change_rate)

    prev_seed_value_l = seed_list_l[i][index]
    prev_seed_value_r = seed_list_r[i][index]

    next_seed_value_l = seed_list_l[i][index+1]
    next_seed_value_r = seed_list_r[i][index+1]

    next_seed_value_2_l = seed_list_l[i][index+2]
    next_seed_value_2_r = seed_list_r[i][index+2]

    a_offset = a - (index * samples_per_change_rate)

    if a_offset + 1000 > samples_per_change_rate:
        samples_after_item_change = (a_offset + 1000) % samples_per_change_rate

        start_value_l = (prev_seed_value_l + (next_seed_value_l-prev_seed_value_l)/samples_per_change_rate * (a_offset % samples_per_change_rate))
        end_value_l = (next_seed_value_l + (next_seed_value_2_l-next_seed_value_l)/samples_per_change_rate * samples_after_item_change)
        start_value_r = (prev_seed_value_r + (next_seed_value_r-prev_seed_value_r)/samples_per_change_rate * (a_offset % samples_per_change_rate))
        end_value_r = (next_seed_value_r + (next_seed_value_2_r-next_seed_value_r)/samples_per_change_rate * samples_after_item_change)

        modifier_list_l = numpy.append(numpy.linspace(start_value_l,next_seed_value_l,num=(1000-samples_after_item_change),endpoint=False),numpy.linspace(next_seed_value_l,end_value_l,num=samples_after_item_change,endpoint=False))
        modifier_list_r = numpy.append(numpy.linspace(start_value_r,next_seed_value_r,num=(1000-samples_after_item_change),endpoint=False),numpy.linspace(next_seed_value_r,end_value_r,num=samples_after_item_change,endpoint=False))
    else:
        start_value_l = (prev_seed_value_l + (next_seed_value_l-prev_seed_value_l)/samples_per_change_rate * (a_offset % samples_per_change_rate))
        end_value_l = (prev_seed_value_l + (next_seed_value_l-prev_seed_value_l)/samples_per_change_rate * (a_offset % samples_per_change_rate + 1000))
        start_value_r = (prev_seed_value_r + (next_seed_value_r-prev_seed_value_r)/samples_per_change_rate * (a_offset % samples_per_change_rate))
        end_value_r = (prev_seed_value_r + (next_seed_value_r-prev_seed_value_r)/samples_per_change_rate * (a_offset % samples_per_change_rate + 1000))

        modifier_list_l = numpy.linspace(start_value_l,end_value_l,num=1000,endpoint=False)
        modifier_list_r = numpy.linspace(start_value_r,end_value_r,num=1000,endpoint=False)

def merge_tracks(output_folder, file_list, seconds_per_change_rate, pan_swirl, file_name_new):
    file_list_handles = []
    file_list_sizes = []

    #open files
    for i in range(0,len(file_list)):
        file_list_handles.append(open(output_folder + file_list[i] + ".wav", 'rb'))
        file_list_sizes.append(len(open(output_folder + file_list[i] + ".wav", 'rb').read()))
    new_file = open(output_folder + file_name_new + ".wav", 'wb')

    #take new header from longest file
    file_size_final = max(file_list_sizes) * 2

    #construct new header with summed file size ("RIFF" + file size minus 8 + some other text + file size minus 44)
    new_header = bytearray([82,73,70,70]) + four_byte(file_size_final - 8) + bytearray([87,65,86,69,102,109,116,32,16,0,0,0,1,0,2,0,68,172,0,0,16,177,2,0,4,0,16,0,100,97,116,97]) + four_byte(file_size_final - 44)
    new_file.write(new_header)

    file_list_bytes = []
    for i in range(0,len(file_list)):
        file_list_bytes.append(file_list_handles[i].read(44))

    #split into 1-sample chunks, write each individually
    for a in range(0,int((file_size_final - 44) / 4)):
        if a % 44100 == 0:
            print_message(str(math.trunc(a/44100)) + " of " + str(math.trunc(((file_size_final - 44) / 4)/44100)) + " seconds rendered")
            
        #every 1000 samples, clear the file_list_bytes list and replace it with the next chunk of 1000 samples (4KB)
        if a % 1000 == 0:
            file_list_bytes = numpy.empty((0,2000))
            for i in range(0,len(file_list)):
                bytes_chunk = list(file_list_handles[i].read(2000))
                file_list_bytes = numpy.append(file_list_bytes, [numpy.append(bytes_chunk, numpy.zeros(2000 - len(bytes_chunk)))],axis=0)

            #convert 2-byte samples to integers
            summed_bytes = ((file_list_bytes[0:len(file_list)+1,1::2] * 256 + file_list_bytes[0:len(file_list)+1,0::2] + 32768) % 65536) - 32768

            #alter volume based on randomised pan seeds
            if pan_swirl == True:
                summed_bytes_l = numpy.empty((len(file_list),1000))
                summed_bytes_r = numpy.empty((len(file_list),1000))
                for i in range(0,len(file_list)):
                    generate_modifiers(a,i,seconds_per_change_rate)
                    summed_bytes_l[i] = summed_bytes[i] * modifier_list_l
                    summed_bytes_r[i] = summed_bytes[i] * modifier_list_r
            else:
                summed_bytes_l = summed_bytes * numpy.reshape(numpy.column_stack(seed_list_l)[0],(len(file_list),1))
                summed_bytes_r = summed_bytes * numpy.reshape(numpy.column_stack(seed_list_r)[0],(len(file_list),1))

            #add values from lists
            layered_samples_l = numpy.sum(summed_bytes_l,axis=0) / int(len(file_list))
            layered_samples_r = numpy.sum(summed_bytes_r,axis=0) / int(len(file_list))

            #convert floats to integers, then back into bytes
            split_bytes = numpy.empty(4000)
            split_bytes[0::4] = layered_samples_l.astype(int) % 256
            split_bytes[1::4] = (layered_samples_l/256).astype(int) % 256
            split_bytes[2::4] = layered_samples_r.astype(int) % 256
            split_bytes[3::4] = (layered_samples_r/256).astype(int) % 256
            split_bytes = split_bytes.astype(numpy.uint8)
            split_bytes = bytearray(split_bytes)

            #write split_bytes to new file
            new_file.write(split_bytes)

def normalise_file(output_folder,input_file,output_file):
    file_a =  open(output_folder + input_file + ".wav", 'rb').read()

    header = file_a[:44]
    file_a = file_a[44:]
    file_a = list(file_a)
    file_a = numpy.array(file_a)

    summed_bytes = numpy.array(((file_a[1::2] * 256 + file_a[0::2] + 32768) % 65536) - 32768)

    amplification_factor = 32768 / abs(max(summed_bytes)) * 0.99

    amplified_bytes = summed_bytes * amplification_factor

    split_bytes = numpy.empty(numpy.size(file_a))
    split_bytes[0::2] = amplified_bytes.astype(int) % 256
    split_bytes[1::2] = (amplified_bytes/256).astype(int) % 256
    split_bytes = split_bytes.astype(numpy.uint8)
    split_bytes = bytearray(split_bytes)

    new_file = open(output_folder + output_file + ".wav", 'wb')
    new_file.write(header + split_bytes)

def commence_brainwashing():
    try:
        compliance_tester = int(track_density_entry.get())
        if compliance_tester < 2:
            tk.messagebox.showerror("Error", "Track density must be 2 or higher")
            return
    except ValueError:
        tk.messagebox.showerror("Error", "Track density must be a whole number")
        return

    try:
        compliance_tester = int(length_entry.get())
        if compliance_tester < 1:
            tk.messagebox.showerror("Error", "Length must be 1 or higher")
            return
    except ValueError:
        tk.messagebox.showerror("Error", "Length must be a whole number")
        return

    if sublim_pan_swirl.get() == True:
        try:
            compliance_tester = int(seconds_per_change_rate_entry.get())
            if compliance_tester < 1:
                tk.messagebox.showerror("Error", "If Pan Movement is on, Seconds per Pan Movement must be 1 or higher")
                return
        except ValueError:
            tk.messagebox.showerror("Error", "If Pan Movement is on, Seconds per Pan Movement must be a whole number")
            return

    if len(sublim_input_files) < 2:
        tk.messagebox.showerror("Error", "Please import at least two input files to generate brainwashings file with")
        return

    if selected_output_folder == "":
        tk.messagebox.showerror("Error", "Please select an output folder")
        return

    if output_file_entry.get() == "":
        tk.messagebox.showerror("Error", "Please give the output file a name")
        return

    if sublim_pan_swirl.get() == True:
        brainwash_me(selected_output_folder + "/",sublim_input_files,output_file_entry.get(),int(length_entry.get()),int(track_density_entry.get()),int(seconds_per_change_rate_entry.get()),sublim_pan_swirl.get())
    else:
        brainwash_me(selected_output_folder + "/",sublim_input_files,output_file_entry.get(),int(length_entry.get()),int(track_density_entry.get()),0,sublim_pan_swirl.get())

def print_message(print_text):
    current_status = tk.Label(root, text=(" "*1000))
    current_status.grid(column=0,row=3,columnspan=9,sticky=tk.NW)
    current_status = tk.Label(root, text=print_text)
    current_status.grid(column=0,row=3,columnspan=9,sticky=tk.NW)
    current_status.wait_visibility()

def brainwash_me(output_folder,input_files,output_file,length,track_density,seconds_per_change_rate, pan_swirl):
    #get lengths of all files
    file_length_list = []
    for i in input_files:
        looking_at_file_for_length = open(i, 'rb').read()
        file_length_list.append(looking_at_file_for_length[7]*(256**3) + looking_at_file_for_length[6]*(256**2) + looking_at_file_for_length[5]*256 + looking_at_file_for_length[4] - 36)

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

    print_message("randomising seeds")
    if pan_swirl == True:
        generate_pan_seeds(track_density, length * 60 / seconds_per_change_rate)
    else:
        generate_pan_seeds(track_density, 1)

    #get a list of the tracks we just generated to put them into the function
    file_layer_list = []
    for i in range(1,track_density+1):
        file_layer_list.append("sublim_track_" + str(i))
    merge_tracks(output_folder,file_layer_list,seconds_per_change_rate,pan_swirl,"sublim_track_quiet")

    print_message("normalising file")
    normalise_file(output_folder,"sublim_track_quiet",output_file)

    print_message("Done")

    for i in range(1,track_density+1):
        os.remove(output_folder + "sublim_track_" + str(i) + ".wav")
    os.remove(output_folder + "sublim_track_quiet.wav")

#setting up the GUI
import tkinter as tk
from tkinter import ttk, filedialog

selected_files  = []
selected_output_folder = str("")

root = tk.Tk()
root.title("SubliminAuthor v1.1 by Drew Ellison")
root.geometry("506x506+50+50")
root.columnconfigure(0,weight=1)
root.columnconfigure(1,weight=1)
root.columnconfigure(2,weight=1)
root.columnconfigure(3,weight=1)
root.columnconfigure(4,weight=1)
root.columnconfigure(5,weight=1)
root.columnconfigure(6,weight=300)

#"Input files" text and browse button
message1 = tk.Label(root, text="Input files:")
message1.grid(column=4,row=0,sticky=tk.W,padx=(10,0))

def open_file():
    global sublim_input_files
    sublim_input_files = filedialog.askopenfilenames(filetypes=[('wav files', '*.wav')])
    message_selected_files = tk.Label(root, text=(chr(10) + " "*1000) *1000)
    message_selected_files.grid(column=0,row=5,columnspan=9, sticky=tk.NW)
    vertical_list = []
    vertical_list = ["Input files:"]
    for x in range(0,len(sublim_input_files)):
        vertical_list.append(chr(10))
        vertical_list.append(sublim_input_files[x])
    message_selected_files = tk.Label(root, text=vertical_list)
    message_selected_files.grid(column=0,row=5,columnspan=9, sticky=tk.NW)

button_browse = ttk.Button(root, text='Browse...', width=10, command=open_file)
button_browse.grid(column=5,row=0, sticky=tk.W)

#"Output folder" text and browse button
message2 = tk.Label(root, text="Output folder:")
message2.grid(column=4,row=1,sticky=tk.W,padx=(10,0))

def select_output_folder():
    global selected_output_folder
    selected_output_folder = filedialog.askdirectory()
    message_selected_output_folder = tk.Label(root, text="Output folder: " + selected_output_folder)
    message_selected_output_folder.grid(column=0,row=4,columnspan=9, sticky=tk.NW)

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
sublim_pan_swirl = tk.BooleanVar()
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