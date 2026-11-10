# 0. Create the cluster

[Lesson map](README.md) · **0. Create the cluster** · [1. The big picture →](01-the-big-picture.md)

In the Docker stages you rented one VM. Today you rent three at once, one in each of three Google
data centres in Warsaw, and Kubernetes runs them as one cluster. You install nothing: every command
runs in Cloud Shell, a Linux terminal inside your browser.

**By the end:** a 3-node cluster called `bugsquash`, a reserved public IP, `kubectl` connected to the
cluster, the course files in Cloud Shell and `bugsquash` as your default namespace.

![What we'll build: a regional GKE cluster in europe-central2 with one e2-medium node in each of the zones a, b and c, each running a frontend and a backend pod, postgres with its 5Gi disk in one zone, a control plane run by Google in all three zones, and a Google Cloud load balancer with the static IP bugsquash-ip in front](images/slides/k8s-00-what-we-build.svg)

## 1. Open Cloud Shell

Why: it already has `gcloud`, `kubectl` and `git`, and it is logged in as you.

Open <https://console.cloud.google.com>, choose your project in the project picker at the top, and
click the **`>_`** icon (*Activate Cloud Shell*) at the top right. A terminal opens at the bottom of
the page. If a window asks you to *Authorize Cloud Shell*, click **Authorize**.

You should see a prompt like `you@cloudshell:~ (your-project-id)$`. These pages shorten it to
`cloudshell$`: type what comes after it, never the prompt itself.

## 2. Choose the project and the region

Why: every later `gcloud` command uses these defaults, and GKE's API must be switched on once per
project. Replace `<PROJECT_ID>` with your project's ID (not its name) from the project picker.

```console
cloudshell$ gcloud config set project <PROJECT_ID>
cloudshell$ gcloud config set compute/region europe-central2
cloudshell$ gcloud services enable container.googleapis.com
```

You should see `Updated property [core/project].`, `Updated property [compute/region].` and, after
up to a minute, `Operation "operations/acf.p2-…" finished successfully.`

## 3. Create the cluster

Why: one command rents three VMs (the *nodes*), installs Kubernetes and adds a control plane run by Google.

```console
cloudshell$ gcloud container clusters create bugsquash --region europe-central2 \
              --num-nodes 1 --machine-type e2-medium --disk-size 30 --release-channel regular
```

| Flag | Meaning |
|------|---------|
| `--region europe-central2` | a *regional* cluster in Warsaw, spread over zones a, b and c |
| `--num-nodes 1` | one node **per zone**, so three nodes in total |
| `--machine-type e2-medium` `--disk-size 30` | 2 shared vCPUs, 4 GB and a 30 GB disk per node, like the course VM |
| `--release-channel regular` | Google upgrades Kubernetes for you, on a tested schedule |

You should see, after about 4 minutes (read the slides of [page 1](01-the-big-picture.md) meanwhile):

```text
Creating cluster bugsquash in europe-central2.......................done.
Created [https://container.googleapis.com/v1/projects/<PROJECT_ID>/zones/europe-central2/clusters/bugsquash].
kubeconfig entry generated for bugsquash.
NAME       LOCATION         MASTER_VERSION      MASTER_IP      MACHINE_TYPE  NODE_VERSION        NUM_NODES  STATUS
bugsquash  europe-central2  1.36.4-gke.2377000  34.118.41.149  e2-medium     1.36.4-gke.2377000  3          RUNNING
```

> [!NOTE]
> **Region and zones.** A region is a city (`europe-central2` is Warsaw); a zone is one data centre
> in it, with its own power and network. One node per zone means a power cut takes out only a third
> of the cluster. Page 9 proves it.

## 4. Reserve a static IP

Why: the public door of page 7 needs an address that never changes, so a DNS name can point at it.
`--global`, because Google's web load balancer is a global one.

```console
cloudshell$ gcloud compute addresses create bugsquash-ip --global
cloudshell$ gcloud compute addresses describe bugsquash-ip --global --format='value(address)'
```

You should see the new address (ours; yours will differ). Write it down:

```text
Created [https://www.googleapis.com/compute/v1/projects/<PROJECT_ID>/global/addresses/bugsquash-ip].
136.81.240.49
```

## 5. Connect kubectl to the cluster

Why: `kubectl` is Kubernetes' remote control, and this stores the cluster's address and your login
in `~/.kube/config` (step 3 already did it; on any other machine you need this command).

```console
cloudshell$ gcloud container clusters get-credentials bugsquash --region europe-central2
cloudshell$ kubectl get nodes
```

You should see three nodes, all `Ready`:

```text
Fetching cluster endpoint and auth data.
kubeconfig entry generated for bugsquash.
NAME                                       STATUS   ROLES    AGE   VERSION
gke-bugsquash-default-pool-23acb34b-32v4   Ready    <none>   26s   v1.36.4-gke.2377000
gke-bugsquash-default-pool-34ca6972-2bt9   Ready    <none>   26s   v1.36.4-gke.2377000
gke-bugsquash-default-pool-7204075e-xh1n   Ready    <none>   25s   v1.36.4-gke.2377000
```

## 6. Get the course files

Why: the YAML files (*manifests*) that describe Bug Squash to Kubernetes are in the course repository.

```console
cloudshell$ git clone https://github.com/Mohammed-Alhuraibi/DevOps_course.git && cd DevOps_course/kubernetes
cloudshell$ ls manifests
```

You should see ten files, from `00-namespace.yaml` to `09-https-redirect.yaml`. Every later command
runs from this `kubernetes` folder.

> [!TIP]
> If `git clone` asks for a username, the repository is private: ask the instructor for access, or
> download the `kubernetes` folder and upload it with Cloud Shell's **⋮ (More) → Upload**.

## 7. Create the namespace

Why: a namespace is a folder inside the cluster. All of Bug Squash goes into `bugsquash`, so one
command deletes it all at the end.

```console
cloudshell$ kubectl apply -f manifests/00-namespace.yaml
cloudshell$ kubectl config set-context --current --namespace=bugsquash
cloudshell$ kubectl get pods
```

You should see:

```text
namespace/bugsquash created
Context "gke_<PROJECT_ID>_europe-central2_bugsquash" modified.
No resources found in bugsquash namespace.
```

The second command makes `bugsquash` your default, so no command in this lesson needs `-n bugsquash`.

## Checkpoint

- `kubectl get nodes` lists three `Ready` nodes.
- You have written down the IP of `bugsquash-ip`.
- `kubectl get pods` answers `No resources found in bugsquash namespace.`

Next: what exactly did you just rent? [1. The big picture](01-the-big-picture.md).

<details>
<summary>Going deeper</summary>

- **From your laptop instead of Cloud Shell.** Install the gcloud CLI
  (<https://cloud.google.com/sdk/docs/install>), run `gcloud init`, then
  `gcloud components install kubectl gke-gcloud-auth-plugin` and step 5's `get-credentials`. If you
  installed gcloud with `apt`, install `kubectl` and `google-cloud-cli-gke-gcloud-auth-plugin` with
  `apt` instead. Read `laptop$` wherever these pages say `cloudshell$`; page 2's Web Preview becomes
  `http://localhost:8080`.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Kubernetes Engine API has not been used in project … or it is disabled` | Run step 2's `gcloud services enable container.googleapis.com`, wait a minute, try again. |
| `Quota 'CPUS' exceeded` | The three nodes need 6 vCPUs. Stop other VMs in the project (the course VM uses 2) or ask for more quota (*IAM & Admin → Quotas*). |
| `The connection to the server localhost:8080 was refused` | kubectl doesn't know the cluster yet: run step 5. |
| Cloud Shell reconnected, or `destination path 'DevOps_course' already exists` | Your files are still there: `cd ~/DevOps_course/kubernetes` (and `git pull` for the latest). kubectl still knows the cluster and the namespace. |
