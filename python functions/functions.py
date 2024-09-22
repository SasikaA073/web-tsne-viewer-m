import numpy as np

# Assuming the following constants are defined:
n_cols = 20
n_rows = 15

# TSNE Values between 0 and 1 
tsne_np_arr = np.random.rand(n_rows * n_cols, 2)

# Functions to test
def get_img_id(row: int, col: int):
    return (row - 1) * n_cols + col

def get_img_row_col(img_id: int):
    row = (img_id // n_cols) if img_id % n_cols == 0 else (img_id // n_cols) + 1
    col = img_id % n_cols if img_id % n_cols != 0 else n_cols
    return row, col

def get_img_tsne(tsne_np_arr: np.array, img_id: int):
    return tsne_np_arr[img_id-1]