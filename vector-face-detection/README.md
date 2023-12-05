Prerequisite:

```bash
pip install tensorflow keras-facenet
```

Launch Surreal

 ```bash
 surreal start --allow-all -u root -p pass -b 127.0.0.1:8000
 ```
 
Index the photos:

```bash
python knn_demo.py
```

Try face recognition:

```bash
python knn_demo.py samples/emmanuel2.jpg
```