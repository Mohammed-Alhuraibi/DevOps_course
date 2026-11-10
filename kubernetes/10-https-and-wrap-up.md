# 10. HTTPS and wrap-up

[Lesson map](README.md) · [← 9. High availability](09-high-availability.md) · **10. HTTPS and wrap-up** · [Cheat sheet](cheatsheet.md)

The game runs in three zones, survives a power cut and updates without downtime. One thing from
Stage 3 is missing: the padlock. On GKE there is no certbot; Google issues and renews the
certificate itself. Then you delete everything, because a cluster costs money every hour it runs.

**By the end:** `https://k8s.gulfheight.com` shows a padlock, HTTP redirects there, the login cookie
is *Secure*, you can map Compose to Kubernetes, and nothing is left running.

> [!NOTE]
> No domain of your own? Watch the instructor do steps 1-4 on `k8s.gulfheight.com`, then go on at
> [From Compose to Kubernetes](#from-compose-to-kubernetes). Your cluster stays on HTTP, and that's
> fine. Outputs marked *expected* are what Google's tools print; our recorded run stopped before them.

## 1. Point the name at the IP and ask for a certificate

Why: Google issues a certificate only for a name that points at your load balancer. A
`ManagedCertificate` names the domain, and one annotation on the Ingress attaches it. Done on
[page 7, step 7](07-ingress.md#7-optional-start-https-now)? Jump to step 2.

In Cloudflare, *DNS → Records → Add record*: type `A`, name `k8s`, IPv4 address = your IP,
**Proxy status: DNS only** (grey cloud). Then:

```console
cloudshell$ dig +short k8s.gulfheight.com @1.1.1.1
cloudshell$ kubectl apply -f manifests/08-https.yaml
```

You should see your IP, then the certificate request and the Ingress updated in place:

```text
136.81.240.49
managedcertificate.networking.gke.io/bugsquash-cert created
ingress.networking.k8s.io/bugsquash configured
```

## 2. Wait for Active

Why: Google checks the name, issues the certificate and installs it on the load balancer, which
takes 15 to 60 minutes.

```console
cloudshell$ kubectl get managedcertificate bugsquash-cert
cloudshell$ curl -sI https://k8s.gulfheight.com/ | head -1
```

You should see (expected) `STATUS` go from empty to `Provisioning` to `Active`, and a few minutes
after `Active` the first HTTPS answer:

```text
NAME             AGE   STATUS
bugsquash-cert   34m   Active
HTTP/2 200
```

Open `https://k8s.gulfheight.com`: padlock.

> [!WARNING]
> **Only now, the redirect.** `09-https-redirect.yaml` sends every `http://` visitor to `https://`.
> Applied before the certificate is `Active`, it sends them to a broken page: we found out in testing.

## 3. Redirect HTTP to HTTPS

Why: like the 301 of Stage 3, no visitor should stay on plain HTTP.

```console
cloudshell$ kubectl apply -f manifests/09-https-redirect.yaml
cloudshell$ curl -sI http://k8s.gulfheight.com/ | grep -iE '^(HTTP|location)'
```

You should see (expected; the redirect needs a few minutes to reach the load balancer):

```text
frontendconfig.networking.gke.io/bugsquash-redirect created
ingress.networking.k8s.io/bugsquash configured
HTTP/1.1 301 Moved Permanently
Location: https://k8s.gulfheight.com/
```

## 4. Secure the login cookie

Why: with HTTPS everywhere, the cookie may be *Secure*. But a ConfigMap change does **not** restart
pods (a container reads its environment once, at start), so you restart the backend yourself.

```console
cloudshell$ kubectl patch configmap bugsquash-config -p '{"data":{"COOKIE_SECURE":"true"}}'
cloudshell$ kubectl rollout restart deployment/backend
cloudshell$ kubectl rollout status deployment/backend --timeout=180s
cloudshell$ kubectl exec deployment/backend -- printenv COOKIE_SECURE
```

You should see (expected, trimmed):

```text
configmap/bugsquash-config patched
deployment.apps/backend restarted
deployment "backend" successfully rolled out
true
```

Log in at `https://k8s.gulfheight.com`: in DevTools (*Application → Cookies*) `bugsquash_token` now
has *Secure* ticked. `patch` was a shortcut: the file still says `"false"`, and applying
`04-config.yaml` again would undo it. In a real project you change the file in Git and apply it.

## From Compose to Kubernetes

![From Compose to Kubernetes: a service in docker-compose.prod.yml becomes a Deployment plus a Service, the nginx proxy and its ports a Service plus an Ingress, the pgdata volume a PersistentVolumeClaim, .env.prod a ConfigMap plus a Secret, healthcheck readiness and liveness probes, restart: unless-stopped a self-healing Deployment, deploy.resources.limits resources requests and limits, and docker compose up -d becomes kubectl apply -f manifests/](images/slides/k8s-11-compose-to-kubernetes.svg)

Nothing today was really new: every line of `docker-compose.prod.yml` has a Kubernetes name. What
is new is that the promise holds across three machines. (In our folder, apply the files one by one:
`manifests/` also holds the lone pod and both HTTPS steps.)

## Clean up

> [!WARNING]
> The cluster, its three nodes, the load balancer, the disk and the static IP cost a few US$ per day
> together, even when nobody plays. See the [pricing calculator](https://cloud.google.com/products/calculator).

Why this order: deleting the namespace first makes Kubernetes remove the load balancer and the disk
it created; then the cluster goes; the IP last.

```console
cloudshell$ kubectl delete namespace bugsquash
cloudshell$ gcloud container clusters delete bugsquash --region europe-central2
cloudshell$ gcloud compute addresses delete bugsquash-ip --global
```

Answer `Y` to each question. You should see (expected; the first two take a few minutes each):

```text
namespace "bugsquash" deleted
Deleting cluster bugsquash...done.
Deleted [https://container.googleapis.com/v1/projects/<PROJECT_ID>/zones/europe-central2/clusters/bugsquash].
Deleted [https://www.googleapis.com/compute/v1/projects/<PROJECT_ID>/global/addresses/bugsquash-ip].
```

Doing the lesson again soon? Skip the last command: a kept IP costs a little, and the DNS record
stays valid. Deleted the IP? Delete the Cloudflare record too.

## What's next

- **Helm** packages these files as one chart with settings: `helm install bugsquash ./chart`.
- **Autoscaling:** a HorizontalPodAutoscaler adds backend pods when the CPU is busy, removes them later.
- **Deploys from Git:** CI applies the files (like Stage 4), or GitOps (Argo CD, Flux) keeps the
  cluster equal to the repository.
- **Cloud SQL:** a managed Postgres with a standby in another zone fixes page 9's weak spot.

## Checkpoint

- HTTPS works with a Google-managed certificate, HTTP redirects to it, and the cookie is *Secure*.
- You can name the Kubernetes object behind every part of the Compose file.
- `gcloud container clusters list` and `gcloud compute addresses list` print nothing for `bugsquash`.

Back to the [lesson map](README.md). Keep the [cheat sheet](cheatsheet.md).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Still `Provisioning` after 60 minutes, or `FailedNotVisible` | `kubectl describe managedcertificate bugsquash-cert`. The name doesn't reach your load balancer: check `dig` (step 1) and the grey cloud. |
| TLS error (`curl: (35)`) right after `Active` | The load balancer is still installing the certificate: wait 5-10 minutes. |
| Login fails on `http://<your IP>` after step 4 | A *Secure* cookie travels only over HTTPS: use `https://k8s.gulfheight.com`. |
| `printenv` still prints `false` | The backend was not restarted: `kubectl rollout restart deployment/backend`. |
| `kubectl delete namespace` seems to hang | It waits while Google deletes the load balancer and the disk: give it a few minutes. |
