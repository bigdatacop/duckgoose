from PIL import Image
import os
import glob
from os import path
import random
from tempfile import TemporaryDirectory
import gzip
import tarfile
import shutil

from google_images_download import google_images_download

def main():

    image_classes = { 'ducks' : 'ducks -rubber' , 'geese' : 'geese' }
    # download_directory = '/home/paperspace/data/downloaded_from_google'
    # output_path = '/home/paperspace/data/ducksgeese/'
    download_directory = '/home/paperspace/tmp/newtmp/google'
    output_path = '/home/paperspace/tmp/newtmp/organised'
                      
    downloadImagesForClasses(image_classes, download_directory, number_of_images=30)

    for image_class in image_classes.keys():
        sanitised_images, cannot_open, one_channel = santityCheckAndOrganiseFromGoogle(image_class, download_directory, output_path)
        partitonIntoTrainValidTest(sanitised_images, image_class, output_path)


def santityCheckAndOrganiseFromGoogle(image_prefix, base_path, output_path):
    """ Check that the images can be opened and that there are three channels. Organise into train/valid/test split by 60/30/10% """
    
    # This is tied to the google download settings: specifically using the prefix == class
    gg = f'{base_path}/**/{image_prefix} *.jpg'

    files = glob.glob(gg, recursive=True)
    outfiles = []
    ioe_error_files = []
    one_channel_files = []

    num = 1
    for ff in files:
        try:
            ii = Image.open(ff)
            number_of_channels = len(ii.getbands())
            
            if number_of_channels == 3:
                outfiles.append(ff)
                num +=1
            else:
                one_channel_files.append(ff)
                print(f'Only one channel: {ff}')
        except IOError as ioe:
            ioe_error_files.append(ff)
            print(f'Error encountered for {ff}: {ioe}')

    return(outfiles, ioe_error_files, one_channel_files)

def partitonIntoTrainValidTest(all_files, prefix, output_path, fraction_train = .6, fraction_valid = 0.3):

    train_files, valid_files, test_files = shuffledSplit(all_files, fraction_train, fraction_valid)

    moveFilesToPath(train_files, output_path, prefix, 'train')
    moveFilesToPath(valid_files, output_path, prefix, 'valid')
    moveFilesToPath(test_files, output_path, prefix, 'test')

def shuffledSplit(all_files, fraction_train, fraction_valid):
    total_number_of_files = len(all_files)

    train_num = round(total_number_of_files * fraction_train)
    valid_num = round(total_number_of_files * fraction_valid)
    test_num = total_number_of_files - train_num - valid_num

    random.shuffle(all_files)

    train_files = all_files[:train_num]
    valid_files = all_files[train_num:(train_num+valid_num)]
    test_files = all_files[(train_num+valid_num):]

    return(train_files, valid_files, test_files)


def moveFilesToPath(files_to_move, output_path, prefix, ml_type):
    this_path = path.join(output_path,ml_type, prefix)
    os.makedirs(this_path, exist_ok=True)
    for tt in files_to_move:
        shutil.copy2(tt, path.join(this_path, path.basename(tt)))


def downloadImagesForClasses(image_classes, download_directory, number_of_images=1000, chromedriver_path='/usr/lib/chromium-browser/chromedriver'):

    if not path.exists(download_directory):
        os.makedirs(download_directory)

    common_arguments = {'limit' : number_of_images, 
            'format' : 'jpg',
            'color_type' : 'full-color',
            'type' : 'photo',
            'output_directory':download_directory,
            'chromedriver': chromedriver_path} # TODO: this shouldn't be hard coded
            
    for image_class, search_term in image_classes.items():
        downloadImagesFor(image_class, search_term, common_arguments)


def downloadImagesFor(keyword, prefix = None, common_arguments = {}):
    if prefix is None:
        prefix = keyword

    search = common_arguments.copy()
    search['keywords'] = keyword
    search['prefix'] = prefix

    resp = google_images_download.googleimagesdownload()
    paths = resp.download(search)

