
Steps (Inside "python function" directory)

1. Copy the images files you need to run the TSNE viewer into "python function/test_images"
2. Create a conda environment with follwoing configuration

```
conda create -n env --name tsne python== 3.11.5```

3. ```pip install -r requirements.txt```

4. Run this one 
```
python3 image_dir_to_atlas.py --input test_images --output test_images
```

5. To get the image embeddings run the follwing 
```python3 pytorch_classify_images.py Output_test_images/test_images_center_cropped/```

6. To get the coordinates json "python3 img_embeddings_to_corrds.py "

7. 


