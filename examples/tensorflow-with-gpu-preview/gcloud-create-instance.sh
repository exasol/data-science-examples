gcloud compute instances create test \
--custom-memory=10GB  \
--custom-cpu=8  \
--accelerator=count=1,type=nvidia-tesla-k80  \
--boot-disk-auto-delete  \
--boot-disk-size=50GB  \
--image=projects/ubuntu-os-cloud/global/images/ubuntu-1804-bionic-v20190514  \
--boot-disk-type=pd-standard  \
--maintenance-policy=TERMINATE  \
--scopes=bigquery,storage-ro,storage-rw  \
--network exasol-integration-demo \
--metadata=startup-script-url=https://raw.githubusercontent.com/tkilias/data-science-examples/tensorflow-gpu-preview/examples/tensorflow-with-gpu-preview/gcloud-setup.sh $*
#--accelerator=count=1,type=nvidia-tesla-v100  \
#--zone=europe-west4-b  \