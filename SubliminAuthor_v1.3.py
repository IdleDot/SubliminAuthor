selected_output_folder = ""
sublim_input_files = []

import math
import random
import os
import numpy

seed_list = numpy.array([])
seed_list_l = numpy.array([])
seed_list_r = numpy.array([])

max_sample = 0

def round_down(x):
    return x - x % 1

def four_byte_to_decimal(a,b,c,d):
    return int(a + (b * 256) + (c * (256**2)) + (d * (256**3)))

def decimal_to_four_byte(x):
    #convert integer file size to a four byte sequence for new file to read
    return bytearray([math.trunc(x) % 256, math.trunc(x/256) % 256, math.trunc(x/(256**2)) % 256, math.trunc(x/(256**3))])

def float32_to_unfloat32(input_file_bytes):
    signs = input_file_bytes[3::4].astype(int) / 128 % 2
    signs = signs - signs % 1
    signs = (-1)**(signs)

    exponents = (
        (input_file_bytes[3::4].astype(int) % 128) * 2 +
        input_file_bytes[2::4].astype(int) / 128 % 2)
    exponents = exponents - exponents % 1
    exponents = 2**(exponents - 127)

    mantissas = (
        (input_file_bytes[2::4].astype(int) % 128) * 2**16 +
        input_file_bytes[1::4].astype(int) * 2**8 +
        input_file_bytes[0::4].astype(int))
    mantissas = mantissas - mantissas % 1
    mantissas = mantissas / 2**23 + 1

    float_samples = signs * exponents * mantissas

    numpy_float_samples = numpy.array(float_samples)
    numpy_integer_samples = (((numpy_float_samples / abs(max(float_samples)) * (256**4-1) / 2) + 256**4/2) % 256**4) - 256**4/2

    split_bytes = numpy.empty(len(float_samples)*4)
    split_bytes[0::4] = numpy_integer_samples.astype(int) % 256
    split_bytes[1::4] = (numpy_integer_samples/256).astype(int) % 256
    split_bytes[2::4] = (numpy_integer_samples/256**2).astype(int) % 256
    split_bytes[3::4] = (numpy_integer_samples/256**3).astype(int) % 256
    split_bytes = split_bytes.astype('uint8')
    return split_bytes

def bit_depth_convert(input_file_bytes, old_bit_depth):
    if old_bit_depth == 8:
        input_file_bytes_new = numpy.empty(len(input_file_bytes) * 2)
        input_file_bytes_new[0::2] = numpy.zeros(len(input_file_bytes))
        input_file_bytes_new[1::2] = (input_file_bytes + 128) % 256
        input_file_bytes = input_file_bytes_new
    elif old_bit_depth % 8 == 0:
        input_file_bytes = numpy.reshape(input_file_bytes,(int(len(input_file_bytes)/int(old_bit_depth / 8)),int(old_bit_depth / 8)))
        input_file_bytes = numpy.delete(input_file_bytes,range(0,int(old_bit_depth / 8 - 2)),axis=1)
        input_file_bytes = numpy.reshape(input_file_bytes,len(input_file_bytes)*2)
    input_file_bytes = input_file_bytes.astype('uint8')
    return input_file_bytes

def stereo_to_mono(input_file_bytes):
    summed_bytes = ((
        (((input_file_bytes[1::4] * 256 + input_file_bytes[0::4] + 32768) % 65536) - 32768) +
        (((input_file_bytes[3::4] * 256 + input_file_bytes[2::4] + 32768) % 65536) - 32768)) / 2)
    summed_bytes = summed_bytes - summed_bytes % 1
    split_bytes = numpy.empty(len(summed_bytes) * 2)
    split_bytes[0::2] = summed_bytes.astype(int) % 256
    split_bytes[1::2] = (summed_bytes/256 - summed_bytes/256 % 1).astype(int) % 256
    split_bytes = split_bytes.astype('uint8')
    return split_bytes

def sample_rate_convert(input_file_bytes, old_sample_rate):
    skipped_samples = []
    for i in range(0,old_sample_rate):
        if math.trunc(i/old_sample_rate * 44100) == math.trunc((i+1)/old_sample_rate * 44100):
            skipped_samples.append(i)

    summed_bytes = ((input_file_bytes[1::2] * 256 + input_file_bytes[0::2] + 32768) % 65536) - 32768
    old_sample_count = len(summed_bytes)

    summed_bytes = numpy.append(summed_bytes, [0]*(old_sample_rate - (old_sample_count % old_sample_rate)))
    filler_bytes = int((old_sample_rate - (old_sample_count % old_sample_rate)) / old_sample_rate * 44100)

    summed_bytes = numpy.reshape(summed_bytes,(int(len(summed_bytes)/old_sample_rate),old_sample_rate))
    summed_bytes = numpy.delete(summed_bytes,skipped_samples,axis=1)
    summed_bytes = numpy.reshape(summed_bytes,len(summed_bytes)*44100)
    summed_bytes = summed_bytes[0:(len(summed_bytes)-filler_bytes)]

    split_bytes = numpy.empty(len(summed_bytes) * 2)
    split_bytes[0::2] = summed_bytes.astype(int) % 256
    split_bytes[1::2] = (summed_bytes/256 - summed_bytes/256 % 1).astype(int) % 256
    split_bytes = split_bytes.astype('uint8')
    return split_bytes

def sample_rate_double(input_file_bytes):
    summed_bytes = ((input_file_bytes[1::2] * 256 + input_file_bytes[0::2] + 32768) % 65536) - 32768
    summed_bytes_offset = numpy.append(summed_bytes[1:],0)
    summed_bytes_2 = (summed_bytes + summed_bytes_offset) / 2
    summed_bytes_2 = summed_bytes_2 - summed_bytes_2 % 1

    split_bytes = numpy.empty(len(summed_bytes) * 4)
    split_bytes[0::4] = summed_bytes.astype(int) % 256
    split_bytes[1::4] = (summed_bytes/256 - summed_bytes/256 % 1).astype(int) % 256
    split_bytes[2::4] = summed_bytes_2.astype(int) % 256
    split_bytes[3::4] = (summed_bytes_2/256 - summed_bytes_2/256 % 1).astype(int) % 256
    split_bytes = split_bytes.astype('uint8')
    return split_bytes

def total_convert(input_file,output_file):
    input_file_handle = open(input_file, 'rb').read()
    new_file = open(output_file, 'wb')

    input_file_bytes_complete = list(input_file_handle)
    input_file_bytes_complete = numpy.array(input_file_bytes_complete)

    for i in range(0,100):
        if (input_file_bytes_complete[i:i+4] == bytearray([100,97,116,97])).all():
            old_header_length = i+8

    old_header = input_file_handle[0:36] + input_file_handle[(old_header_length-8):old_header_length]
    input_file_bytes = input_file_handle[old_header_length:]
    input_file_bytes = numpy.array(list(input_file_bytes))
    old_file_size = four_byte_to_decimal(old_header[4],old_header[5],old_header[6],old_header[7]) + 8

    file_size_total = old_file_size - old_header_length

    if old_header[20:22] == bytearray([3,0]):
        input_file_bytes = float32_to_unfloat32(input_file_bytes)

    if old_header[34:36] != bytearray([16,0]):
        input_file_bytes = bit_depth_convert(input_file_bytes, int(old_header[34]))
        file_size_total = file_size_total / int(old_header[34]) * 16
         
    if old_header[22:24] == bytearray([2,0]):
        input_file_bytes = stereo_to_mono(input_file_bytes)
        file_size_total = file_size_total / 2

    progressive_sample_rate = four_byte_to_decimal(old_header[24],old_header[25],old_header[26],old_header[27])

    if progressive_sample_rate != 44100:
        while progressive_sample_rate < 44100:
            input_file_bytes = sample_rate_double(input_file_bytes)
            progressive_sample_rate = progressive_sample_rate * 2
            file_size_total = file_size_total * 2
        if progressive_sample_rate > 44100:
            input_file_bytes = sample_rate_convert(input_file_bytes, progressive_sample_rate)
            file_size_total = file_size_total / progressive_sample_rate * 44100

    file_size_total = file_size_total + 44

    new_header = (
        bytearray([82,73,70,70]) +
        decimal_to_four_byte(file_size_total - 8) +
        bytearray([87,65,86,69,102,109,116,32,16,0,0,0,1,0,1,0,68,172,0,0,136,88,1,0,2,0,16,0,100,97,116,97]) +
        decimal_to_four_byte(file_size_total - 44))

    input_file_bytes = input_file_bytes.astype('uint8')

    new_header = bytearray(new_header)
    input_file_bytes = bytearray(input_file_bytes)

    new_file.write(new_header + input_file_bytes)

def append_files(file_list, file_name_new):
    file_list_bytes = []
    file_list_sizes = []

    new_file = open(file_name_new, 'wb')

    #open files and note their sizess (based on bytes 5-8 of each files)
    for i in range(0,len(file_list)):
        file_list_bytes.append(open(file_list[i], 'rb').read())
        file_list_sizes.append(
            four_byte_to_decimal(
                file_list_bytes[i][4],
                file_list_bytes[i][5],
                file_list_bytes[i][6],
                file_list_bytes[i][7]) + 8)

    file_size_total = sum(file_list_sizes)
    
    #write new header with summed file size to new file ("RIFF" + file size minus 8 + some other text + file size minus 44)
    new_file.write(
        bytearray([82,73,70,70]) +
        decimal_to_four_byte(file_size_total - 8) +
        bytearray([87,65,86,69,102,109,116,32,16,0,0,0,1,0,1,0,68,172,0,0,136,88,1,0,2,0,16,0,100,97,116,97]) +
        decimal_to_four_byte(file_size_total - 44))

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

        start_value_l = (
            prev_seed_value_l + 
            (next_seed_value_l-prev_seed_value_l)/samples_per_change_rate * (a_offset % samples_per_change_rate))
        end_value_l = (
            next_seed_value_l + 
            (next_seed_value_2_l-next_seed_value_l)/samples_per_change_rate * samples_after_item_change)
        start_value_r = (
            prev_seed_value_r +
            (next_seed_value_r-prev_seed_value_r)/samples_per_change_rate * (a_offset % samples_per_change_rate))
        end_value_r = (
            next_seed_value_r +
            (next_seed_value_2_r-next_seed_value_r)/samples_per_change_rate * samples_after_item_change)

        modifier_list_l = numpy.append(
            numpy.linspace(start_value_l,next_seed_value_l,num=(1000-samples_after_item_change),endpoint=False),
            numpy.linspace(next_seed_value_l,end_value_l,num=samples_after_item_change,endpoint=False))
        modifier_list_r = numpy.append(
            numpy.linspace(start_value_r,next_seed_value_r,num=(1000-samples_after_item_change),endpoint=False),
            numpy.linspace(next_seed_value_r,end_value_r,num=samples_after_item_change,endpoint=False))
    else:
        start_value_l = (prev_seed_value_l + (next_seed_value_l-prev_seed_value_l)/samples_per_change_rate * (a_offset % samples_per_change_rate))
        end_value_l = (prev_seed_value_l + (next_seed_value_l-prev_seed_value_l)/samples_per_change_rate * (a_offset % samples_per_change_rate + 1000))
        start_value_r = (prev_seed_value_r + (next_seed_value_r-prev_seed_value_r)/samples_per_change_rate * (a_offset % samples_per_change_rate))
        end_value_r = (prev_seed_value_r + (next_seed_value_r-prev_seed_value_r)/samples_per_change_rate * (a_offset % samples_per_change_rate + 1000))

        modifier_list_l = numpy.linspace(start_value_l,end_value_l,num=1000,endpoint=False)
        modifier_list_r = numpy.linspace(start_value_r,end_value_r,num=1000,endpoint=False)

def merge_tracks(file_list, seconds_per_change_rate, pan_swirl, output_file):
    global progress_bar
    global max_sample

    file_list_handles = []
    file_list_sizes = []

    #open files
    for i in range(0,len(file_list)):
        file_list_handles.append(open(os.path.dirname(output_file) + "\\" + file_list[i] + ".wav", 'rb'))
        file_list_sizes.append(len(open(os.path.dirname(output_file) + "\\" + file_list[i] + ".wav", 'rb').read()))
        file_list_handles[i].seek(44)
    new_file = open(output_file, 'wb')

    #take new header from longest file
    file_size_final = max(file_list_sizes) * 2

    #construct new header with summed file size ("RIFF" + file size minus 8 + some other text + file size minus 44)
    new_header = bytearray([82,73,70,70]) + decimal_to_four_byte(file_size_final - 8) + bytearray([87,65,86,69,102,109,116,32,16,0,0,0,1,0,2,0,68,172,0,0,16,177,2,0,4,0,16,0,100,97,116,97]) + decimal_to_four_byte(file_size_final - 44)
    new_file.write(new_header)

    #split into 1000-sample chunks, write each individually
    for a in range(0,int((file_size_final - 44) / 4))[0::1000]:
        #clear the file_list_bytes list and replace it with the next chunk of 1000 samples (4KB)
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

        layered_samples_l = layered_samples_l - layered_samples_l % 1
        layered_samples_r = layered_samples_r - layered_samples_r % 1

        if max(abs(layered_samples_l)) > max_sample:
            max_sample = max(abs(layered_samples_l))

        if max(abs(layered_samples_r)) > max_sample:
            max_sample = max(abs(layered_samples_r))

        #convert floats to integers, then back into bytes
        split_bytes = numpy.empty(4000)
        split_bytes[0::4] = layered_samples_l.astype(int) % 256
        split_bytes[1::4] = (layered_samples_l/256 - layered_samples_l/256 % 1).astype(int) % 256
        split_bytes[2::4] = layered_samples_r.astype(int) % 256
        split_bytes[3::4] = (layered_samples_r/256 - layered_samples_r/256 % 1).astype(int) % 256
        split_bytes = split_bytes.astype(numpy.uint8)
        split_bytes = bytearray(split_bytes)

        #write split_bytes to new file
        new_file.write(split_bytes)

        #print progress if this loop crosses a one-second barrier
        if math.trunc((a-1000)/44100) != math.trunc(a/44100):
            print_message(str(math.trunc(a/44100)) + " of " + str(math.trunc(((file_size_final - 44) / 4)/44100)) + " seconds rendered")
            progress_bar['value'] = progress_bar['value'] + (1 / math.trunc(((file_size_final - 44) / 4)/44100) * merge_weight)
        
        if cancel_mode == 1:
            return

def normalise_file(input_file,output_file):
    global progress_bar
    global cancel_mode
    global merge_weight

    file_handle =  open(input_file, 'rb')
    new_file = open(output_file, 'wb')

    header = file_handle.read(44)
    new_file.write(header)

    file_size = (four_byte_to_decimal(header[4],header[5],header[6],header[7]) + 8)

    amplification_factor = 32768 / max_sample * 0.99

    for a in range(0,file_size - 44)[0::1000]:
        bytes_chunk = list(file_handle.read(1000))
        input_file_bytes = numpy.append(bytes_chunk, numpy.zeros(1000 - len(bytes_chunk)))
        input_file_bytes = list(input_file_bytes)
        input_file_bytes = numpy.array(input_file_bytes)

        summed_bytes = numpy.array(((input_file_bytes[1::2] * 256 + input_file_bytes[0::2] + 32768) % 65536) - 32768)

        amplified_bytes = summed_bytes * amplification_factor

        amplified_bytes = amplified_bytes - amplified_bytes % 1

        split_bytes = numpy.empty(1000)
        split_bytes[0::2] = amplified_bytes.astype(int) % 256
        split_bytes[1::2] = (amplified_bytes/256 - amplified_bytes/256 % 1).astype(int) % 256
        split_bytes = split_bytes.astype(numpy.uint8)
        split_bytes = bytearray(split_bytes)

        new_file.write(split_bytes)

        if math.trunc((a-1000)/44100 / 4) != math.trunc(a/44100 / 4):
            print_message(str(math.trunc(a/44100/4)) + " of " + str(math.trunc((file_size - 44)/44100/4)) + " seconds normalised")
            progress_bar['value'] = progress_bar['value'] + (1 / math.trunc((file_size - 44)/44100/4) * normalise_weight)

        if cancel_mode == 1:
            return

def commence_brainwashing():
    try:
        compliance_tester = int(track_density_entry.get())
        if compliance_tester < 2:
            tk.messagebox.showerror("Error", "Track density must be 2 or higher")
            return
        if compliance_tester > 24:
            result = tk.messagebox.askquestion("Warning","Are you sure you want to export a file with over 25 tracks? (This will cause more lag than usual)")
            if result == "no":
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

    output_file_name = filedialog.asksaveasfile(defaultextension=".wav",filetypes=[("wav files","*.wav")])

    if sublim_pan_swirl.get() == True:
        brainwash_me(
            sublim_input_files,
            output_file_name.name,
            int(length_entry.get()),
            int(track_density_entry.get()),
            int(seconds_per_change_rate_entry.get()),
            sublim_pan_swirl.get())
    else:
        brainwash_me(
            sublim_input_files,
            output_file_name.name,
            int(length_entry.get()),
            int(track_density_entry.get()),
            0,
            sublim_pan_swirl.get())

def print_message(print_text):
    current_status = tk.Label(root, text=print_text + " "*50)
    current_status.grid(column=0,row=27,columnspan=9,sticky=tk.NW)
    current_status.wait_visibility()

def brainwash_me(input_files,output_file,length,track_density,seconds_per_change_rate, pan_swirl):
    global total_weight
    global convert_weight
    global append_weight
    global merge_weight
    global normalise_weight
    global progress_bar
    global brainwash_button
    global cancel_mode

    progress_bar = ttk.Progressbar(root,orient="horizontal",mode="determinate",length=344)
    progress_bar.grid(column=0,row=26,columnspan=9,sticky=tk.NW,padx=(10,10))

    progress_bar['value'] = 0

    brainwash_button.grid_forget()

    cancel_button = ttk.Button(root,text="Cancel",width=56,command=cancel)
    cancel_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))

    total_weight = ((len(input_files) * 0.1) + (length * 60 * track_density * 0.022) + (length * 60 * 0.06)) / 100

    convert_weight = (len(input_files) * 0.1) / total_weight
    append_weight = (length * 60 * track_density * 0.002) / total_weight
    merge_weight = (length * 60 * track_density * 0.02) / total_weight
    normalise_weight = (length * 60 * 0.06) / total_weight

    print_message("0 of " + str(len(input_files)) + " files converted")
    input_files_converted = []
    for i in range(0,len(input_files)):
        input_files_converted.append(os.path.dirname(output_file) + "\\sublim_converted_" + str(i) + ".wav")
        total_convert(input_files[i],input_files_converted[i])
        print_message(str(i) + " of " + str(len(input_files)) + " files converted")
        progress_bar['value'] = progress_bar['value'] + (1 / len(input_files) * convert_weight)
        if cancel_mode == 1:
            cancel_button.grid_forget()
            brainwash_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))
            cancel_mode = 0
            return

    #get lengths of all files
    file_length_list = []
    for i in input_files_converted:
        looking_at_file_for_length = open(i, 'rb').read()
        file_length_list.append(
            looking_at_file_for_length[7]*(256**3) +
            looking_at_file_for_length[6]*(256**2) +
            looking_at_file_for_length[5]*256 +
            looking_at_file_for_length[4] - 36)
        if cancel_mode == 1:
            cancel_button.grid_forget()
            brainwash_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))
            cancel_mode = 0
            return

    #for every required track, generate a random list of files from input_files until it's long enough, then append into one audio file
    print_message("0 of " + str(track_density) + " tracks generated")
    for i in range(1,track_density+1):
        track_content_list = []
        track_length = 0
        while track_length < (length * 2 * 60 * 44100):
            randomiser = random.randrange(0,len(input_files_converted))
            track_content_list.append(input_files_converted[randomiser])
            track_length = track_length + file_length_list[randomiser]
        append_files(track_content_list,os.path.dirname(output_file) + "\\sublim_track_" + str(i) + ".wav")
        print_message(str(i) + " of " + str(track_density) + " tracks generated")
        progress_bar['value'] = progress_bar['value'] + (1/track_density * append_weight)
        if cancel_mode == 1:
            cancel_button.grid_forget()
            brainwash_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))
            cancel_mode = 0
            return

    print_message("randomising seeds")
    if pan_swirl == True:
        generate_pan_seeds(track_density, length * 60 / seconds_per_change_rate)
    else:
        generate_pan_seeds(track_density, 1)
    
    if cancel_mode == 1:
        cancel_button.grid_forget()
        brainwash_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))
        cancel_mode = 0
        return

    #get a list of the tracks we just generated to put them into the function
    file_layer_list = []
    for i in range(1,track_density+1):
        file_layer_list.append("sublim_track_" + str(i))
    merge_tracks(file_layer_list,seconds_per_change_rate,pan_swirl,os.path.dirname(output_file) + "\\sublim_track_quiet.wav")

    if cancel_mode == 1:
        cancel_button.grid_forget()
        brainwash_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))
        cancel_mode = 0
        return

    print_message("normalising file")
    normalise_file(os.path.dirname(output_file) + "\\sublim_track_quiet.wav",output_file)

    if cancel_mode == 1:
        cancel_button.grid_forget()
        brainwash_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))
        cancel_mode = 0
        return

    print_message("Done")

    for i in range(0,len(input_files)):
        os.remove(os.path.dirname(output_file) + "\\sublim_converted_" + str(i) + ".wav")
    for i in range(1,track_density+1):
        os.remove(os.path.dirname(output_file) + "\\sublim_track_" + str(i) + ".wav")
    os.remove(os.path.dirname(output_file) + "\\sublim_track_quiet.wav")

    cancel_button.grid_forget()
    brainwash_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))

def cancel():
    global cancel_mode
    cancel_mode = 1

#setting up the GUI
import tkinter as tk
from tkinter import ttk, filedialog

selected_files  = []
selected_output_folder = str("")
sublim_input_files = []

page = 1
cancel_mode = 0

root = tk.Tk()
root.title("SubliminAuthor v1.3 by Drew Ellison")
root.geometry("364x680+50+50")

def open_file():
    global sublim_input_files
    global page
    sublim_input_files = sublim_input_files + list(filedialog.askopenfilenames(filetypes=[('wav files', '*.wav')]))
    delete_buttons()
    load_page(1)

def try_to_load_page(x):
    global sublim_input_files
    if x == 0:
        return
    elif (x-1)*20+1 > len(sublim_input_files):
        return
    else:
        load_page(x)

def load_page(x):
    global page
    delete_labels()
    delete_buttons()
    for i in range((x-1)*20,x*20):
        if i < len(sublim_input_files):
            generate_label(i)
            generate_button(i)

    page = x

    tk.Label(root, text= "Page " + str(x) + " of " + str(math.trunc((len(sublim_input_files)-1)/20) + 1)).grid(column=1,row=24,padx=(31,0))

labels = []
buttons = []

def generate_label(x):
    global labels
    labels.append("")
    labels[x%20] = tk.Label(root, text=sublim_input_files[x][len(os.path.dirname(sublim_input_files[x]))+1:len(sublim_input_files[x])])
    labels[x%20].grid(column=0,row=4+(x%20),columnspan=3,sticky=tk.NW)

def delete_labels():
    global labels
    for i in range(0,len(labels)):
        labels[i].destroy()
    labels = []

def generate_button(x):
    global buttons
    buttons.append("")
    buttons[x%20] = ttk.Button(root, text="x",width=2,command=lambda: delete_file(x))
    buttons[x%20].grid(column=3,row=4+(x%20),sticky=tk.NE)

def delete_buttons():
    global buttons
    for i in range(0,len(buttons)):
        buttons[i].grid_forget()
    buttons = []

def delete_file(x):
    global page
    global sublim_input_files
    del sublim_input_files[x]
    load_page(page)

#"Input files" button
ttk.Button(root, text='Import files...', width=56, command=open_file).grid(column=0,row=2,columnspan=7,sticky=tk.W,padx=(10,0))
tk.Label(root, text="Input files:").grid(column=0,row=3,columnspan=2,sticky=tk.NW)

#Track Density field
tk.Label(root, text="Track Density: ").grid(column=0,row=0,sticky=tk.W,padx=(10,0))
track_density_entry = ttk.Entry(root,width=16)
track_density_entry.grid(column=0,row=1,sticky=tk.W,padx=(10,0))

#Length field
tk.Label(root, text="Length (mins):").grid(column=1,row=0,sticky=tk.W,padx=(10,0))
length_entry = ttk.Entry(root,width=16)
length_entry.grid(column=1,row=1,sticky=tk.W,padx=(10,0))

#Pan Movement field
sublim_pan_swirl = tk.BooleanVar()
tk.Label(root, text="Secs/Movement: ").grid(column=2,row=0,columnspan=2,sticky=tk.W,padx=(10,0))
seconds_per_change_rate_entry = ttk.Entry(root,width=16)
seconds_per_change_rate_entry.grid(column=2,row=1,sticky=tk.W,padx=(10,0))
pan_movement_checkbox = ttk.Checkbutton(root,variable=sublim_pan_swirl,onvalue=True,offvalue=False)
pan_movement_checkbox.grid(column=3,row=1,sticky=tk.W)

#Brainwash Button
brainwash_button = ttk.Button(root,text="Brainwash Me!",width=56,command=commence_brainwashing)
brainwash_button.grid(column=0,row=25,columnspan=7,sticky=tk.W,padx=(10,0))

#Prev. Page Button
ttk.Button(root,text="Prev. Page",width=15,command=lambda: try_to_load_page(page-1)).grid(column=0,row=24,sticky=tk.NW,padx=(10,0))

#Next Page Button
ttk.Button(root,text="Next Page",width=15,command=lambda: try_to_load_page(page+1)).grid(column=2,row=24,columnspan=2,sticky=tk.NE,padx=(0,3))

root.mainloop()
