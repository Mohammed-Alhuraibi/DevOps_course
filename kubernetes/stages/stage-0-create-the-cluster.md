# Stage 0: Create the cluster

[Kubernetes lesson](../README.md) · [Concepts](../concepts.md) · **Stage 0** · [Stage 1 →](stage-1-explore-the-cluster.md)

In the Docker stages you rented one VM. Today you rent three at once, one in each of three Google
data centres in Warsaw, and Kubernetes runs them as one cluster. You create it in the Google Cloud
console, where you can see every part, and drive it from your own laptop with `kubectl`.

**By the end:** a Standard regional cluster called `bugsquash` with 3 nodes, a reserved static IP,
`kubectl` on your laptop connected to the cluster, the course files cloned and `bugsquash` as your
default namespace.

![What we'll build: a regional GKE cluster in europe-central2 with one e2-medium node in each of the zones a, b and c, each running a frontend and a backend pod, postgres with its 5Gi disk in one zone, a control plane run by Google in all three zones, and a Google Cloud load balancer with the static IP bugsquash-ip in front](../images/slides/k8s-00-what-we-build.svg)

## 1. Create the cluster in the console

Why: the console shows every setting on one page, and you change only a few of them.

In <https://console.cloud.google.com>, pick your project, then **Kubernetes Engine → Clusters →
Create** (click **Enable** if the console asks for the Kubernetes Engine API). Choose **Standard**.

> [!WARNING]
> **Standard, not Autopilot.** Autopilot hides the nodes, so Stage 9's demo, stopping a node, is impossible.

| Setting | Value |
|---------|-------|
| Name | `bugsquash` |
| Location type | **Regional**, region `europe-central2` (zones a, b and c by default) |
| Release channel | Regular (the default) |
| **NODE POOLS → default-pool → Number of nodes (per zone)** | **1**, NOT the default 3 (it counts per zone, so 3 nodes in all) |
| **default-pool → Nodes**: machine type | `e2-medium` (2 shared vCPUs and 4 GB, like the course VM) |
| **default-pool → Nodes**: boot disk size | **30** GB |
| Everything else | the default |

> [!WARNING]
> **Number of nodes is per zone.** Left at the default 3, a regional cluster gets 3 × 3 = **9 nodes**:
> nine public IPs (more than a free-trial project allows: *Insufficient quota, IP Addresses 113%*) and
> three times the cost. With **1**, you get 3 nodes, one per zone.

Click **Create**. You should see `bugsquash` in the list with a spinner, then a green check, 3
nodes and version `1.36.x` (about 4 minutes in our test). Read [Stage 1](stage-1-explore-the-cluster.md)'s
slides meanwhile.

> [!NOTE]
> **Region and zones.** A region is a city (`europe-central2` is Warsaw); a zone is one data centre
> in it, with its own power and network. One node per zone means a power cut takes out only a third
> of the cluster. Stage 9 proves it.

## 2. Reserve a static IP in the console

Why: the public door of Stage 7 needs an address that never changes, so a DNS name can point at it.
Google's web load balancer is global, so the address must be global too.

**VPC network → IP addresses → Reserve external static IP address**: name `bugsquash-ip`, IP
version **IPv4**, type **Global**, then **Reserve**.

You should see `bugsquash-ip` in the list with its address (ours: `136.81.240.49`), with nothing yet
under **In use by**. Write the address down: every new reservation gets a different one.

> [!NOTE]
> **Then what? Nothing yet, on purpose.** You have only *booked* the address, like a parking spot
> with your name on it; the cluster does not know about it and does not need to. In
> [Stage 7](stage-7-ingress.md#2-open-the-door) the Ingress file asks for the spot **by its name**,
> with one line: `kubernetes.io/ingress.global-static-ip-name: bugsquash-ip`. GKE then builds a Google
> load balancer on exactly this address, and *In use by* then shows that load balancer.
> So the name must be exactly `bugsquash-ip`.

**Instructor, for HTTPS later:** point the domain at the address now, so DNS is ready long before
Stage 10. In Cloudflare: an `A` record `k8s` → this address, **DNS only** (grey cloud).

## 3. Install the tools on your laptop (once)

Why: `kubectl` is Kubernetes' remote control, and the Google Cloud CLI logs it in with your account.

Install the Google Cloud CLI (<https://cloud.google.com/sdk/docs/install>). On Windows, use WSL
(Ubuntu) and its Linux instructions, so that every command in this lesson works as written. Then:

```console
laptop$ gcloud components install kubectl gke-gcloud-auth-plugin
laptop$ gcloud auth login
laptop$ gcloud config set project <PROJECT_ID>
```

`<PROJECT_ID>` is the project's ID (not its name), shown in the console's project picker. Installed
the CLI with apt, dnf or Homebrew, and `gcloud components` refuses? Install `kubectl` and
`google-cloud-cli-gke-gcloud-auth-plugin` with that package manager instead.

You should see the components installed, a browser tab where you sign in to Google, then
`You are now logged in as [you@example.com].` and `Updated property [core/project].`

## 4. Connect kubectl to the cluster

Why: this writes the cluster's address and your login into `~/.kube/config`.

In the console, open **Kubernetes Engine → Clusters → bugsquash** and click **Connect**: it shows
the exact command. Copy it, then check the nodes:

```console
laptop$ gcloud container clusters get-credentials bugsquash --region europe-central2 --project <PROJECT_ID>
laptop$ kubectl get nodes
```

You should see three nodes, all `Ready` (names differ for you):

```text
Fetching cluster endpoint and auth data.
kubeconfig entry generated for bugsquash.
NAME                                       STATUS   ROLES    AGE   VERSION
gke-bugsquash-default-pool-23acb34b-32v4   Ready    <none>   26s   v1.36.4-gke.2377000
gke-bugsquash-default-pool-34ca6972-2bt9   Ready    <none>   26s   v1.36.4-gke.2377000
gke-bugsquash-default-pool-7204075e-xh1n   Ready    <none>   25s   v1.36.4-gke.2377000
```

**Look in the console:** the cluster's **Nodes** tab lists the same three nodes, with their zones.

## 5. Get the course files

Why: the YAML files (*manifests*) that describe Bug Squash to Kubernetes are in the course repository.

```console
laptop$ git clone https://github.com/Mohammed-Alhuraibi/DevOps_course.git && cd DevOps_course/kubernetes
laptop$ ls manifests
```

You should see ten files, from `00-namespace.yaml` to `09-https-redirect.yaml`. Every later command
runs from this `kubernetes` folder.

> [!TIP]
> If `git clone` asks for a username, the repository is private: ask the instructor for access, or
> download it as a ZIP from GitHub (**Code → Download ZIP**) and unpack it.

## 6. Create the namespace

Why: a namespace is a folder inside the cluster. All of Bug Squash goes into `bugsquash`, so one
command deletes it all at the end.

```console
laptop$ kubectl apply -f manifests/00-namespace.yaml
laptop$ kubectl config set-context --current --namespace=bugsquash
laptop$ kubectl get pods
```

You should see:

```text
namespace/bugsquash created
Context "gke_<PROJECT_ID>_europe-central2_bugsquash" modified.
No resources found in bugsquash namespace.
```

The second command makes `bugsquash` your default, so no command in this lesson needs `-n bugsquash`.

> [!IMPORTANT]
> **Don't skip this step.** Without it, everything you create lands in the namespace `default`: the app
> still works, but Stage 10's one-line cleanup deletes nothing and the load balancer keeps costing money.
> Check any time: `kubectl config view --minify | grep namespace` must say `namespace: bugsquash`.

## Checkpoint

- The console shows `bugsquash` with a green check, and `kubectl get nodes` lists three `Ready` nodes.
- You have written down the address of `bugsquash-ip`.
- `kubectl get pods` answers `No resources found in bugsquash namespace.`

Next: what exactly did you just rent? [Stage 1: The big picture](stage-1-explore-the-cluster.md).

<details>
<summary>Going deeper: the same thing with commands, or in Cloud Shell</summary>

- **Steps 1 and 2 as commands.** These created the cluster of our tested run (about 4 minutes):

  ```console
  laptop$ gcloud services enable container.googleapis.com
  laptop$ gcloud container clusters create bugsquash --region europe-central2 \
            --num-nodes 1 --machine-type e2-medium --disk-size 30 --release-channel regular
  laptop$ gcloud compute addresses create bugsquash-ip --global
  laptop$ gcloud compute addresses describe bugsquash-ip --global --format='value(address)'
  ```

- **Cloud Shell.** The **`>_`** icon at the top right of the console opens a terminal in the browser
  with `gcloud`, `kubectl` and `git` preinstalled and already logged in: skip step 3 and type the
  same commands there. Stage 2's `localhost:8080` then becomes **Web Preview → Preview on port 8080**.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| *Insufficient quota*: **IP Addresses 113%** when you click Create | Number of nodes was left at 3 per zone (9 nodes). Set **NODE POOLS → default-pool → Number of nodes (per zone)** to **1**; the estimate drops to a third and the quota fits. |
| `command not found: gcloud` (or `kubectl`) | The CLI is installed but your shell does not know its folder yet. Open a **new** terminal; if that does not help, add it to your shell's start file, for example `echo 'source ~/google-cloud-sdk/path.zsh.inc' >> ~/.zshrc` (bash: `path.bash.inc` and `~/.bashrc`; use the folder you installed to), then open a new terminal. |
| The console asks to enable the Kubernetes Engine API | Click **Enable**, wait a minute, then **Create** again. |
| Creating fails with a quota error for CPUs | The three nodes need 6 vCPUs. Stop other VMs in the project (the course VM uses 2) or ask for more quota (*IAM & Admin → Quotas*). |
| `gke-gcloud-auth-plugin … was not found or is not executable` | Install the plugin (step 3), open a new terminal, run step 4 again. |
| `The connection to the server localhost:8080 was refused` | kubectl doesn't know the cluster yet: run step 4. |
| `get-credentials`: `403` or `Not found` | Wrong project or account: `gcloud auth login` again and check `<PROJECT_ID>` in the command. |
