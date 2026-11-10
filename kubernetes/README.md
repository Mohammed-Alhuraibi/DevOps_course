# Introduction to Kubernetes: Bug Squash Arena on GKE

[Course README](../README.md) · Before this lesson: [Containers and Docker](../docs/containers-and-docker.md)

In the Docker stages one VM ran the whole game, and when that VM stopped, the game stopped. Today
the same images move to a Kubernetes cluster: three machines in three Google data centres, run as
one. You will start a single pod, then let Kubernetes keep copies alive, give them a stable name, a
database disk and a public door, update them while visitors play, and finally switch a machine off
in the middle of the class to see the game keep running. Every idea gets one slide and a few
commands with Bug Squash.

![What we'll build: visitors reach k8s.gulfheight.com over HTTPS through a Google Cloud load balancer with the static IP bugsquash-ip, made by the Ingress bugsquash, which sends /api to the backend and / to the frontend; inside a regional GKE cluster in europe-central2, three e2-medium nodes in zones a, b and c each run a frontend and a backend pod, and one zone also runs postgres with its 5Gi disk; Google runs the control plane in all three zones and kubectl on your laptop talks to it; the ConfigMap bugsquash-config, the Secret bugsquash-secrets and the claim postgres-data live in the cluster too](images/slides/k8s-00-what-we-build.svg)

## The pages

| Page | Concept | Hands-on | ≈ min |
|------|---------|----------|:-----:|
| [0. Create the cluster](00-create-the-cluster.md) | GKE, Cloud Shell, namespaces | a 3-zone cluster, a static IP, the course files | 15 |
| [1. The big picture](01-the-big-picture.md) | control plane and worker nodes | find both halves in your own cluster | 10 |
| [2. Pods](02-pods.md) | the smallest thing Kubernetes runs | run the frontend, look inside, open it in the browser | 12 |
| [3. Deployments](03-deployments.md) | desired state, self-healing | kill a pod, scale to 5, apply the file again | 12 |
| [4. Services](04-services.md) | one stable name, load balancing | call `frontend` by name, count who answers | 10 |
| [5. ConfigMaps and Secrets](05-configmaps-and-secrets.md) | settings outside the image | create the Secret, then decode it | 8 |
| [6. Storage and the backend](06-storage-and-the-backend.md) | persistent volumes | Postgres on a Google disk, the *survivor* test | 12 |
| [7. Ingress](07-ingress.md) | the one public door | a Google load balancer, play in your browser | 12 |
| [8. Rolling updates](08-rolling-updates.md) | updates without downtime | v1 → v2 → v1 under live traffic | 12 |
| [9. High availability](09-high-availability.md) | zones and failover | switch a node off while a loop calls the API | 15 |
| [10. HTTPS and wrap-up](10-https-and-wrap-up.md) | managed certificates, Compose → Kubernetes | the padlock, then delete everything | 10 |
| | | **Total** | **≈ 2 h** |

## How the pages work

- Every command runs in **Google Cloud Shell**, a terminal in your browser, shown as `cloudshell$`.
  From page 0, step 6 on, you stay in the `DevOps_course/kubernetes` folder.
- Each page: a short story, a slide, numbered steps (*Why*, the command, *You should see*), a
  checkpoint and a troubleshooting table.
- The outputs come from a real run on a regional GKE cluster on 10 November 2026. Your node names,
  pod names, IPs and ages will differ; the shape will not.
- Each file in [`manifests/`](manifests/) explains itself in its comments, which name the page that uses it.

## What you need

- A Google Cloud project with billing enabled (free-trial credit works) in which you are Owner or
  Editor.
- A browser. Nothing to install: Cloud Shell already has `gcloud`, `kubectl` and `git`.
- The [Docker lesson](../docs/containers-and-docker.md): images, containers, volumes and Compose.
- For HTTPS only: a domain in Cloudflare. The course uses `k8s.gulfheight.com`; without a domain you
  watch that part on the instructor's screen.

> [!WARNING]
> **Cost.** A regional cluster with three `e2-medium` nodes, a load balancer, a disk and a static IP
> costs a few US$ per day, even when nobody plays. [Clean up](10-https-and-wrap-up.md#clean-up)
> after class.

## Before class (instructor)

1. Push the `kubernetes/` folder to the repository's default branch, so that `git clone` (page 0,
   step 6) gives students this folder.
2. About an hour before class, run page 0 for your demo cluster (the cluster takes about 4 minutes)
   and reserve `bugsquash-ip`. Point `k8s.gulfheight.com` at that IP in Cloudflare (*DNS only*).
3. The Ingress (page 7) needs about 5 minutes for its address and 7 until the site answers: apply it,
   then explain the slide while Google builds.
4. Apply `08-https.yaml` right after page 7 ([page 7, step 7](07-ingress.md#7-optional-start-https-now)):
   the certificate takes 15-60 minutes, so it is *Active* by page 10.
5. Before the high-availability demo, check which zone Postgres runs in, and stop a node in a
   **different** zone ([page 9, step 2](09-high-availability.md#2-find-the-databases-zone)). Our
   test stopped one node; with two stopped, everything must fit on the last `e2-medium`, so rehearse
   that before showing it.

## Cheat sheet

[cheatsheet.md](cheatsheet.md): the everyday `kubectl` commands of this lesson and the four `gcloud`
commands, on one page.

**Start:** [0. Create the cluster](00-create-the-cluster.md)
