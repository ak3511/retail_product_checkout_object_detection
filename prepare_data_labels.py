import boxx
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import os
from matplotlib import pyplot as plt
from PIL import Image
import time
from tqdm import tqdm

# # Functions
def get_json_images_df(json_file_path):

    json = boxx.loadjson(json_file_path)

    json_images_df = pd.DataFrame(json['images'])

    json_images_df = json_images_df.rename(columns={'height':'image_height',
                                                    'width':'image_width',
                                                    'id':'image_id'})

    json_images_df = json_images_df[['file_name','image_width','image_height','image_id']]

    return json_images_df


def get_json_annotations_df(json_file_path):

    json = boxx.loadjson(json_file_path)

    json_annotations_df = pd.DataFrame(json['annotations'])

    json_annotations_df = json_annotations_df.rename(columns={'area':'image_area',
                                                              'bbox':'image_bbox',
                                                              'point_xy':'image_point_xy',
                                                              'segmentation':'image_segmentation',
                                                              'iscrowd':'is_crowded'})

    json_annotations_df = json_annotations_df[['image_id','image_area','image_bbox','image_point_xy',
                                               'image_segmentation','is_crowded','category_id']]

    return json_annotations_df


def get_json_items_df(json_file_path):

    json = boxx.loadjson(json_file_path)

    json_items_df = pd.DataFrame(json['__raw_Chinese_name_df'])

    json_items_df = json_items_df[['sku_name','category_id','sku_class','code',
                                   'shelf','num','name','clas','known','ind']]

    return json_items_df


def get_json_df(json_file_path, data_dir):

    json_images_df = get_json_images_df(json_file_path)
    json_annotations_df = get_json_annotations_df(json_file_path)

    json_df = json_images_df.merge(json_annotations_df,
                                   how='left',
                                   left_on='image_id',
                                   right_on='image_id')

    json_df.insert(0, 'data_directory', data_dir)

    return json_df


def get_yolo_annotations(image_width, image_height, image_bbox):

    x_min = image_bbox[0]
    y_min = image_bbox[1]
    x_max = image_bbox[0] + image_bbox[2]
    y_max = image_bbox[1] + image_bbox[3]
    x = (x_min + x_max) / 2.0 / image_width
    y = (y_min + y_max) / 2.0 / image_height
    w = (x_max - x_min) / image_width
    h = (y_max - y_min) / image_height

    yolo_bbox = [x, y, w, h]

    return yolo_bbox


def write_yolo_annotation_to_txt(json_df, data_dir):
    
    array_of_file_name = json_df['file_name'].unique()
    
    for i in tqdm(range(len(array_of_file_name))):
        file_name = array_of_file_name[i]
        array_of_yolo_annotation = json_df[json_df['file_name'] == file_name]['yolo_annotation'].values

        f = open(data_dir + str.replace(file_name, '.jpg', '.txt'), "w+")

        for i in range(len(array_of_yolo_annotation)):
            if i < len(array_of_yolo_annotation):
                f.write(str(array_of_yolo_annotation[i][0]) + ' ' +
                        str(array_of_yolo_annotation[i][1]) + ' ' +
                        str(array_of_yolo_annotation[i][2]) + ' ' +
                        str(array_of_yolo_annotation[i][3]) + ' ' +
                        str(array_of_yolo_annotation[i][4]))
                f.write('\n')
            else:
                f.write(str(array_of_yolo_annotation[i][0]) + ' ' +
                        str(array_of_yolo_annotation[i][1]) + ' ' +
                        str(array_of_yolo_annotation[i][2]) + ' ' +
                        str(array_of_yolo_annotation[i][3]) + ' ' +
                        str(array_of_yolo_annotation[i][4]))

        f.close()


def write_img_file_path_to_txt(data_dir, txt_name):

    file_list = os.listdir(os.path.join(os.getcwd(), data_dir))
    file_list = [data_dir + f for f in file_list if f.endswith(".jpg")]

    f = open(data_dir + txt_name, "w+")

    for i in range(len(file_list)):
        if i < len(file_list):
            f.write(str(file_list[i]))
            f.write('\n')
        else:
            f.write(str(file_list[i]))

    f.close()


def from_yolo_to_cor(box, shape):
    img_h, img_w, _ = shape
    # x1, y1 = ((x + witdth)/2)*img_width, ((y + height)/2)*img_height
    # x2, y2 = ((x - witdth)/2)*img_width, ((y - height)/2)*img_height
    x1, y1 = int((box[0] + box[2]/2)*img_w), int((box[1] + box[3]/2)*img_h)
    x2, y2 = int((box[0] - box[2]/2)*img_w), int((box[1] - box[3]/2)*img_h)
    return x1, y1, x2, y2


def draw_boxes(img, boxes, shape):
    for box in boxes:
        x1, y1, x2, y2 = from_yolo_to_cor(box, shape)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 3)
    plt.imshow(img)


if __name__ == '__main__':
    train_json_file_path = 'data/instances_train2019.json'
    val_json_file_path = 'data/instances_val2019.json'
    test_json_file_path = 'data/instances_test2019.json'

    json_items_df = get_json_items_df(train_json_file_path)
    json_items_df.to_csv('data/json_items_df.csv', index=False)

    retinanet_class_map_df = json_items_df[['name']].copy()
    retinanet_class_map_df['id'] = np.arange(0,len(retinanet_class_map_df['name']))
    retinanet_class_map_df.to_csv('retinanet_class_map_df.csv', index=False)

    item_names = json_items_df['name'].values
    f = open('data/retail-product-checkout.names', "w+", encoding='utf-8')
    for i in range(len(item_names)):
        if i < len(item_names):
            f.write(item_names[i])
            f.write('\n')
        else:
            f.write(item_names[i])
    f.close()

    train_json_df = get_json_df(train_json_file_path, 'data/train2019/')
    train_json_df = train_json_df.merge(json_items_df[['category_id','name','ind']],
                                        how='left',
                                        left_on='category_id',
                                        right_on='category_id')
    train_json_df['file_path'] = train_json_df['data_directory'] + train_json_df['file_name']
    train_json_df['x1'] = train_json_df['image_bbox'].apply(lambda x: int(x[0]))
    train_json_df['y1'] = train_json_df['image_bbox'].apply(lambda x: int(x[1]))
    train_json_df['x2'] = train_json_df['image_bbox'].apply(lambda x: int(x[0] + x[2]))
    train_json_df['y2'] = train_json_df['image_bbox'].apply(lambda x: int(x[1] + x[3]))

    retinanet_train_df = train_json_df[['file_path','x1','y1','x2','y2','name']].copy()
    retinanet_train_df.to_csv('data/retinanet_train_df.csv', index=False)

    train_json_df['yolo_bbox'] = train_json_df[['image_width','image_height','image_bbox']].apply(lambda x: get_yolo_annotations(x[0],x[1],x[2]),axis=1)
    train_json_df['yolo_annotation'] = train_json_df['ind'].apply(lambda x: [x]) + train_json_df['yolo_bbox']
    train_json_df.to_csv('data/train_json_df.csv', index=False)
    write_yolo_annotation_to_txt(train_json_df,'data/train2019/')
    write_img_file_path_to_txt('data/', 'train.txt')

    val_json_df = get_json_df(val_json_file_path, 'data/val2019/')
    val_json_df = val_json_df.merge(json_items_df[['category_id','name','ind']],
                                        how='left',
                                        left_on='category_id',
                                        right_on='category_id')
    val_json_df['file_path'] = val_json_df['data_directory'] + val_json_df['file_name']
    val_json_df['x1'] = val_json_df['image_bbox'].apply(lambda x: int(x[0]))
    val_json_df['y1'] = val_json_df['image_bbox'].apply(lambda x: int(x[1]))
    val_json_df['x2'] = val_json_df['image_bbox'].apply(lambda x: int(x[0] + x[2]))
    val_json_df['y2'] = val_json_df['image_bbox'].apply(lambda x: int(x[1] + x[3]))

    retinanet_val_df = val_json_df[['file_path','x1','y1','x2','y2','name']].copy()
    retinanet_val_df.to_csv('data/retinanet_val_df.csv', index=False)

    val_json_df['yolo_bbox'] = val_json_df[['image_width','image_height','image_bbox']].apply(lambda x: get_yolo_annotations(x[0],x[1],x[2]),axis=1)
    val_json_df['yolo_annotation'] = val_json_df['ind'].apply(lambda x: [x]) + val_json_df['yolo_bbox']
    val_json_df.to_csv('data/val_json_df.csv', index=False)
    write_yolo_annotation_to_txt(val_json_df, 'data/val2019/')
    write_img_file_path_to_txt('data', 'validation.txt')

    test_json_df = get_json_df(test_json_file_path, 'data/test2019/')
    test_json_df = test_json_df.merge(json_items_df[['category_id','name','ind']],
                                        how='left',
                                        left_on='category_id',
                                        right_on='category_id')
    test_json_df['file_path'] = test_json_df['data_directory'] + test_json_df['file_name']
    test_json_df['x1'] = test_json_df['image_bbox'].apply(lambda x: int(x[0]))
    test_json_df['y1'] = test_json_df['image_bbox'].apply(lambda x: int(x[1]))
    test_json_df['x2'] = test_json_df['image_bbox'].apply(lambda x: int(x[0] + x[2]))
    test_json_df['y2'] = test_json_df['image_bbox'].apply(lambda x: int(x[1] + x[3]))

    retinanet_test_df = test_json_df[['file_path','x1','y1','x2','y2','name']].copy()
    retinanet_test_df.to_csv('data/retinanet_test_df.csv', index=False)
    
    test_json_df['yolo_bbox'] = test_json_df[['image_width','image_height','image_bbox']].apply(lambda x: get_yolo_annotations(x[0],x[1],x[2]),axis=1)
    test_json_df['yolo_annotation'] = test_json_df['ind'].apply(lambda x: [x]) + test_json_df['yolo_bbox']
    test_json_df.to_csv('data/test_json_df.csv', index=False)
    write_yolo_annotation_to_txt(test_json_df, 'data/test2019/')
    write_img_file_path_to_txt('data', 'test.txt')


    # # Select particular image and display bounding box
    # i = 612
    # img = np.array(Image.open(os.path.join('data/val2019/',val_json_df['file_name'].values[i])))
    #
    # draw_boxes(img, list(val_json_df['yolo_bbox'][val_json_df['image_id']==val_json_df['image_id'].values[i]]),
    #            (val_json_df['image_height'].values[i],
    #             val_json_df['image_width'].values[i],
    #             3))
