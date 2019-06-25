NAME=$1
shift
gcloud compute instances create $NAME \
--custom-memory=30GB  \
--custom-cpu=8  \
--boot-disk-auto-delete  \
--boot-disk-size=200GB  \
--image=projects/ubuntu-os-cloud/global/images/ubuntu-1804-bionic-v20190514  \
--boot-disk-type=pd-standard  \
--maintenance-policy=TERMINATE  \
--scopes=bigquery,storage-ro,storage-rw  \
--metadata=startup-script-url=https://raw.githubusercontent.com/exasol/data-science-examples/master/examples/tensorflow-with-gpu-preview/gcloud-setup.sh $*
