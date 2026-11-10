# Kubernetes concepts

[Kubernetes lesson](README.md) · **Concepts** · [Hands-on: Stage 0 →](stages/stage-0-create-the-cluster.md)

You already know containers and Docker Compose. Kubernetes runs those same containers on many machines
at once and keeps them healthy for you. Eleven slides are the whole theory (about 25 minutes); then
the hands-on stages build every idea with Bug Squash Arena.

## What we'll build

![What we'll build: a regional GKE cluster in europe-central2 with one e2-medium node in each of the zones a, b and c, each running a frontend and a backend pod, postgres with its 5Gi disk in one zone, a control plane run by Google in all three zones, and a Google Cloud load balancer with the static IP bugsquash-ip in front](images/slides/k8s-00-what-we-build.svg)

Our game on Google Kubernetes Engine: one address, one load balancer, and three machines in three
zones, each running a copy of the frontend and the backend; the database keeps its data on a disk.
Every box in this picture is built, step by step, in the stages.

## 1. Why Kubernetes?

![Why Kubernetes: with Docker Compose on one VM the site dies with the VM, and scaling and updates are done by hand; a Kubernetes cluster spreads pods over three machines, starts a new pod when one dies, scales from 3 to 5 copies with one line and updates one pod at a time; like a thermostat set to 21 degrees, you write replicas: 3 and Kubernetes keeps 3 copies running](images/slides/k8s-01-why-kubernetes.svg)

With Docker Compose, the whole game lives on one VM: when that VM dies, the game dies, and scaling or
updating means typing commands by hand. Kubernetes works like a **thermostat**: you write down what
you want (`replicas: 3`), and it keeps checking reality and fixing every difference, across many machines.

**Hands-on:** [Stage 3](stages/stage-3-deployments.md): kill a pod and watch it come back.

## 2. Brain and workers

![The cluster as a restaurant: the control plane is the manager, run by Google on GKE, with the API server as the front desk every request goes through, the scheduler that picks a node for every new pod, the controller manager that keeps reality equal to the plan, and etcd, the notebook with the whole cluster's state; kubectl on your laptop talks only to the API server; three worker nodes are the cooks, each with a kubelet that follows the manager's orders, containerd that runs the containers and kube-proxy that routes Service traffic](images/slides/k8s-02-brain-and-workers.svg)

A cluster has two halves. The **control plane** is the brain (the API server, the scheduler, the
controllers and etcd, its notebook): it decides. The **worker nodes** are ordinary VMs that run the
containers. On GKE, Google runs the brain for you, with a copy in each of three zones, and `kubectl` on
your laptop only ever talks to its API server.

**Hands-on:** [Stage 1](stages/stage-1-explore-the-cluster.md): find both halves in your own cluster.

## 3. Pods

![Pods: a pod is the shell around one container, like a pea pod around its pea, with an optional helper container and its own IP address; 01-pod.yaml shows the four parts of every Kubernetes file: apiVersion and kind say what it is, metadata gives the name hello-frontend and the label app: hello, spec says what you want, the frontend image sha-0902b98 on port 8080; kubectl delete pod hello-frontend removes it for good, because a lone pod is never brought back](images/slides/k8s-03-pods.svg)

A **pod** is the smallest thing Kubernetes runs: one container (sometimes a few helpers with it) with
its own IP address. Pods are mortal: delete one and it is gone for good, which is why you rarely
create pods yourself.

**Hands-on:** [Stage 2](stages/stage-2-pods.md): run the frontend as one pod, look inside, delete it.

## 4. Deployments

![Deployments: the Deployment frontend with replicas: 3 owns a ReplicaSet that owns three pods; when one crashes, the controller starts a new copy, because its control loop compares the desired state, 3 copies from your YAML, with the actual state, 2 running, every few seconds and fixes the difference; kubectl scale deployment frontend --replicas=5 changes the goal to five copies](images/slides/k8s-04-deployments.svg)

A **Deployment** keeps a number of identical pods alive. Its controller compares the desired state
(3 copies) with the actual one, again and again: a pod dies, a new one starts within seconds; change 3
to 5 and two more appear.

**Hands-on:** [Stage 3](stages/stage-3-deployments.md): self-healing and scaling.

## 5. Services

![Services: the Ingress for /api and any pod calling http://backend:3000 reach the Service backend, which selects the pods labelled app=backend and spreads the calls over them; a replaced pod gets a new IP but the Service name stays, like a company phone number that any free agent answers; inside the cluster DNS turns the name backend into the Service's fixed IP](images/slides/k8s-05-services.svg)

Pods come and go with new names and IPs. A **Service** is one stable name, like `backend`, that
forwards to whichever ready pods carry the right label and spreads the load over them, like a company
phone number that rings any free agent.

**Hands-on:** [Stage 4](stages/stage-4-services.md): call `frontend` by name and count who answers.

## 6. ConfigMaps and Secrets

![ConfigMaps and Secrets: the .env.prod file of the Docker stages splits into the ConfigMap bugsquash-config with the plain settings NODE_ENV, COOKIE_SECURE, TRUST_PROXY, POSTGRES_DB, PGHOST, PGPORT, PGUSER and PGDATABASE, and the Secret bugsquash-secrets with POSTGRES_PASSWORD and JWT_SECRET; the unchanged backend image gets every ConfigMap key through envFrom, and PGPASSWORD and JWT_SECRET from the Secret, all as environment variables; a Secret is base64, not encryption: echo c2VjcmV0 | base64 -d prints secret](images/slides/k8s-06-configmaps-and-secrets.svg)

Settings stay out of the image, so the same image runs everywhere. A **ConfigMap** holds ordinary
settings, a **Secret** holds passwords: the `.env.prod` of the Docker stages, split in two. Careful:
a Secret is only base64-encoded, not encrypted.

**Hands-on:** [Stage 5](stages/stage-5-configmaps-and-secrets.md): create both, then decode the Secret.

## 7. Storage

![Storage: the deleted postgres pod and its replacement both show the PersistentVolumeClaim postgres-data, 5 GiB, ReadWriteOnce, bound to a PersistentVolume that is a Google Persistent Disk living outside every pod; like a cloakroom, the claim is the ticket, the volume is the coat and any pod with the ticket gets the same coat back; ReadWriteOnce means one node writes at a time, so the database runs as one pod with the Recreate strategy](images/slides/k8s-07-storage.svg)

Pods are disposable; data is not. A **PersistentVolumeClaim** is a cloakroom ticket: whichever pod
shows the ticket gets the same coat, here a Google Persistent Disk, even after the old pod is gone.

**Hands-on:** [Stage 6](stages/stage-6-storage-and-the-backend.md): delete the database pod, keep the players.

## 8. Ingress

![Ingress: the browser at k8s.gulfheight.com reaches a Google Cloud load balancer with the static IP bugsquash-ip, made from the Ingress bugsquash, the one public door; /api, the API calls from the game, goes to the Service backend:3000 and its three pods, and /, the HTML, CSS and JS files, to the Service frontend:8080 and its three pods; it is the job the nginx proxy did in the Docker stages, and Google issues and renews the HTTPS certificate instead of certbot](images/slides/k8s-08-ingress.svg)

One public door for the whole app, like the nginx proxy of the Docker stages. On GKE an **Ingress**
becomes a real Google load balancer with one static IP: `/api` goes to the backend, everything else to
the frontend.

**Hands-on:** [Stage 7](stages/stage-7-ingress.md): get the address and play in your browser.

## 9. Rolling updates

![Rolling updates in four steps: three v1 frontend pods (sha-0902b98); a v2 pod (sha-dcb0790) becomes ready, then a v1 pod stops; the same again; finally three v2 pods; traffic never stops because the Service only sends visitors to ready pods, and the game's footer shows which commit is live; kubectl set image deployment/frontend starts the update and kubectl rollout undo deployment/frontend brings v1 back](images/slides/k8s-09-rolling-updates.svg)

Kubernetes replaces pods one at a time, v1 to v2, and sends visitors to a new pod only once it is
ready, so nobody sees a broken page. Something wrong with v2? `kubectl rollout undo` goes back.

**Hands-on:** [Stage 8](stages/stage-8-rolling-updates.md): update while a loop keeps calling the site.

## 10. High availability

![High availability: frontend and backend pods are spread over zones a, b and c behind the Google load balancer, which sends visitors only to ready pods; the instructor stops the node in zone b and, after about 30 seconds, Kubernetes re-creates its two pods on the nodes in zones a and c; the control plane is replicated by Google in all three zones; the honest weak spot is the single Postgres pod with its disk in one zone, so stop a node in another zone, and use Cloud SQL in production](images/slides/k8s-10-high-availability.svg)

The copies live in three zones, three different data centres. Switch a machine off: the copies
elsewhere keep serving, and Kubernetes re-creates the lost pods within about 30 seconds. The weak
spot, honestly: our single database pod.

**Hands-on:** [Stage 9](stages/stage-9-high-availability.md): stop a node in the middle of the class.

## 11. From Compose to Kubernetes

![From Compose to Kubernetes: a service in docker-compose.prod.yml becomes a Deployment plus a Service, the nginx proxy and its ports a Service plus an Ingress, the pgdata volume a PersistentVolumeClaim, .env.prod a ConfigMap plus a Secret, healthcheck readiness and liveness probes, restart: unless-stopped a self-healing Deployment, deploy.resources.limits resources requests and limits, and docker compose up -d becomes kubectl apply -f manifests/](images/slides/k8s-11-compose-to-kubernetes.svg)

Everything you know from Compose has a Kubernetes name: a service becomes a Deployment plus a Service,
volumes become claims, `.env.prod` becomes a ConfigMap and a Secret, healthchecks become probes, and
`docker compose up -d` becomes `kubectl apply -f`.

**Hands-on:** [Stage 10](stages/stage-10-https-and-wrap-up.md): HTTPS, the recap and cleaning up.

## Words to remember

| Word | In one line |
|------|-------------|
| **Cluster** | a control plane plus worker nodes, run as one computer |
| **Node** | one worker machine (a VM) that runs pods |
| **Pod** | one or more containers with one IP; the smallest thing Kubernetes runs |
| **Deployment** | keeps N identical pods running, and updates them one by one |
| **Service** | a stable name and load balancer in front of changing pods |
| **ConfigMap / Secret** | settings / passwords, given to pods as environment variables |
| **PersistentVolumeClaim** | a request for a disk that outlives any pod |
| **Ingress** | the public door: routes outside traffic to Services |
| **Namespace** | a folder inside the cluster (ours: `bugsquash`) |
| **Label** | a sticky note like `app=frontend`; Services and Deployments find pods by it |
| **kubectl** | the command-line remote control for the cluster |
| **Manifest** | a YAML file that describes what you want; `kubectl apply -f` sends it |

**Next:** the hands-on stages. Start with [Stage 0: Create the cluster](stages/stage-0-create-the-cluster.md).
