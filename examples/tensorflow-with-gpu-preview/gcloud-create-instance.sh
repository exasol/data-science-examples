gcloud compute instances create test \
--accelerator=count=1,type=nvidia-tesla-v100  \
--boot-disk-auto-delete  \
--boot-disk-size=50GB  \
--zone=europe-west4-b  \
--image=projects/ubuntu-os-cloud/global/images/ubuntu-1804-bionic-v20190514  \
--boot-disk-type=pd-standard  \
--maintenance-policy=TERMINATE  \
--scopes=bigquery,storage-ro,storage-rw  \

--metadata=startup-script-url=<URL>
