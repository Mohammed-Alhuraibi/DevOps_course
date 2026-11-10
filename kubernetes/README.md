# Introduction to Kubernetes: Bug Squash Arena on GKE

[Course README](../README.md) · Before this lesson: [Containers and Docker](../docs/containers-and-docker.md)

In the Docker stages one VM ran the whole game, and when that VM stopped, the game stopped. Today
the same images move to a Kubernetes cluster: three machines in three Google data centres, run as
one. You will start a single pod, then let Kubernetes keep copies alive, give them a stable name, a
database disk and a public door, update them while visitors play, and finally switch a machine off
in the middle of the class to see the game keep running. Every idea gets one slide and a few
commands with Bug Squash.

![What we'll build: visitors reach k8s.gulfheight.com over HTTPS through a Google Cloud load balancer with the static IP bugsquash-ip, made by the Ingress bugsquash, which sends /api to the backend and / to the frontend; inside a regional GKE cluster in europe-central2, three e2-medium nodes in zones a, b and c each run a frontend and a backend pod, and one zone also runs postgres with its 5Gi disk; Google runs the control plane in all three zones and kubectl on your laptop talks to it; the ConfigMap bugsquash-config, the Secret bugsquash-secrets and the claim postgres-data live in the cluster too](images/slides/k8s-00-what-we-build.svg)

## The lesson in two parts

**Part 1: Concepts, about 25 minutes.** [concepts.md](concepts.md): eleven slides, one idea each, in
plain words. No commands yet. This is the "theory first" part, like
[Containers and Docker](../docs/containers-and-docker.md).

**Part 2: Hands-on stages, about 2 hours.** Every concept again, this time with Bug Squash Arena on a
real cluster:

| Stage | Concept | Hands-on | ≈ min |
|:-----:|---------|----------|:-----:|
| [0](stages/stage-0-create-the-cluster.md) | the cluster | create it in the console, connect `kubectl` on your laptop | 15 |
| [1](stages/stage-1-explore-the-cluster.md) | brain and workers | find both halves in your own cluster | 5 |
| [2](stages/stage-2-pods.md) | pods | run the frontend, look inside, open it in the browser | 12 |
| [3](stages/stage-3-deployments.md) | deployments | kill a pod, scale to 5, apply the file again | 12 |
| [4](stages/stage-4-services.md) | services | call `frontend` by name, count who answers | 10 |
| [5](stages/stage-5-configmaps-and-secrets.md) | ConfigMaps and Secrets | create the Secret, then decode it | 8 |
| [6](stages/stage-6-storage-and-the-backend.md) | storage | Postgres on a Google disk, the *survivor* test | 12 |
| [7](stages/stage-7-ingress.md) | ingress | a Google load balancer, play in your browser | 12 |
| [8](stages/stage-8-rolling-updates.md) | rolling updates | v1 → v2 → v1 under live traffic | 12 |
| [9](stages/stage-9-high-availability.md) | high availability | switch a node off while a loop calls the API | 15 |
| [10](stages/stage-10-https-and-wrap-up.md) | HTTPS and wrap-up | the padlock, Compose → Kubernetes, delete everything | 10 |

## How the stages work

- Commands run in **your laptop's terminal**, shown as `laptop$`. From Stage 0, step 5 on, you stay in
  the `DevOps_course/kubernetes` folder.
- Clicks happen in the **Google Cloud console** (<https://console.cloud.google.com>): creating the
  cluster, stopping a node, cleaning up. **Look in the console** lines show where to *see* what a
  command just did.
- Each stage: a short story, its slide again, numbered steps (*Why*, the command, *You should see*), a
  checkpoint and a troubleshooting table.
- The outputs come from a real run on a regional GKE cluster on 10 November 2026. Your node names,
  pod names, IPs and ages will differ; the shape will not.
- Each file in [`manifests/`](manifests/) explains itself in its comments, which name the stage that uses it.

## What you need

- A Google Cloud project with billing enabled (free-trial credit works) in which you are Owner or
  Editor.
- A laptop with a bash-style terminal (macOS, Linux, or WSL on Windows), `git` and a browser. Stage 0
  installs the Google Cloud CLI and `kubectl` (once, about 10 minutes).
- The [Docker lesson](../docs/containers-and-docker.md): images, containers, volumes and Compose.
- For HTTPS only: a domain in Cloudflare. The course uses `k8s.gulfheight.com`; without a domain you
  watch that part on the instructor's screen.

> [!WARNING]
> **Cost.** A regional cluster with three `e2-medium` nodes, a load balancer, a disk and a static IP
> costs a few US$ per day, even when nobody plays. [Clean up](stages/stage-10-https-and-wrap-up.md#clean-up)
> after class.

## Before class (instructor)

> [!NOTE]
> **Rehearsing on Autopilot?** Fine for Stages 1-8, with two differences: `kubectl get nodes` shows
> nothing until you deploy something (Autopilot creates nodes for your pods), and you cannot stop a node,
> so Stage 9 needs a **Standard** cluster.

1. Push the `kubernetes/` folder to the repository's default branch, so that `git clone` (Stage 0,
   step 5) gives students this folder. Ask students to do Stage 0, step 3 (installing the tools) at
   home: it is the slowest part.
2. About an hour before class, create your demo cluster and `bugsquash-ip` in the console (Stage 0,
   steps 1-2; the cluster takes about 4 minutes) and connect your laptop (steps 3-4).
3. A static IP is **new every time** you reserve it: point the Cloudflare `A` record for
   `k8s.gulfheight.com` at the address the console shows now (*DNS only*), not at last time's.
4. The Ingress (Stage 7) needs about 5 minutes for its address and 7 until the site answers: apply it,
   then explain the slide while Google builds.
5. Apply `08-https.yaml` right after Stage 7 ([Stage 7, step 7](stages/stage-7-ingress.md#7-optional-start-https-now)):
   the certificate takes 15-60 minutes, so it is *Active* by Stage 10.
6. Before the high-availability demo, check which zone Postgres runs in, and stop a node in a
   **different** zone ([Stage 9, step 2](stages/stage-9-high-availability.md#2-find-the-databases-zone)). Our
   test stopped one node; with two stopped, everything must fit on the last `e2-medium`, so rehearse
   that before showing it.

## Cheat sheet

[cheatsheet.md](cheatsheet.md): the everyday `kubectl` commands of this lesson, the one `gcloud`
command you need in class, and where to click in the console, on one page.

**Start:** [Part 1: Concepts](concepts.md), then [Stage 0: Create the cluster](stages/stage-0-create-the-cluster.md).
