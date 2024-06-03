.PHONY: notebook
notebook:
	pdm run jupyter notebook --no-browser --ip=0.0.0.0 --port=9991 --NotebookApp.token='' --NotebookApp.password=''
