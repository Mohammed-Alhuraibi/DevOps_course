# 7. Ingress

[Lesson map](README.md) · [← 6. Storage and the backend](06-storage-and-the-backend.md) · **7. Ingress** · [8. Rolling updates →](08-rolling-updates.md)

Everything runs, but only inside the cluster. In the Docker stages one nginx proxy was the only
container with public ports. On GKE that job goes to an Ingress: you write a few lines of routing
rules, and Google builds a real cloud load balancer on your static IP. Building takes minutes, so
you start it first and talk while it builds.

**By the end:** you play Bug Squash at `http://<your IP>` in your browser, and the backend's logs show
your own public IP.

![Ingress: the browser at k8s.gulfheight.com reaches a Google Cloud load balancer with the static IP bugsquash-ip, made from the Ingress bugsquash, the one public door; /api, the API calls from the game, goes to the Service backend:3000 and its three pods, and /, the HTML, CSS and JS files, to the Service frontend:8080 and its three pods; it is the job the nginx proxy did in the Docker stages, and Google issues and renews the HTTPS certificate instead of certbot](images/slides/k8s-08-ingress.svg)

## 1. Check your static IP

Why: the Ingress asks for the address by its name, `bugsquash-ip`; without it there is no load balancer.

**Look in the console:** **VPC network → IP addresses** must list `bugsquash-ip`, type *Global*.
Missing? Reserve it ([page 0, step 2](00-create-the-cluster.md#2-reserve-a-static-ip-in-the-console)).
Then keep its address in a variable of your terminal, for the commands below:

```console
laptop$ IP=<your IP>
laptop$ echo $IP
```

You should see your address (ours: `136.81.240.49`). In a new terminal window, set `IP` again.

## 2. Open the door

Why: two rules, like the nginx proxy had: `/api…` goes to the backend Service, everything else to
the frontend Service.

```console
laptop$ kubectl apply -f manifests/07-ingress.yaml
```

You should see: `ingress.networking.k8s.io/bugsquash created`.

## 3. Wait for Google

Why: Google is now building a load balancer: a front door on your IP, the two path rules, health
checks copied from your readiness probes, and direct links to your pods' IPs. That takes minutes.

```console
laptop$ kubectl get ingress bugsquash --watch
```

`--watch` prints a new line whenever the Ingress changes. You should see `ADDRESS` filled in after
about 5 minutes (trimmed); then press **Ctrl+C**:

```text
NAME        CLASS    HOSTS   ADDRESS         PORTS   AGE
bugsquash   <none>   *       136.81.240.49   80      4m49s
```

**Look in the console:** **Kubernetes Engine → Gateways, Services & Ingress → Ingress** shows
`bugsquash` with a spinner, then a green check and your IP; in **VPC network → IP addresses**,
`bugsquash-ip` is now *in use by* a forwarding rule.

> [!TIP]
> **Get a coffee.** In our run the address appeared after about 5 minutes and the site answered
> after about 7. Until then Google answers with an error page (`404` or `502`): normal, not your
> mistake. Instructors: a good moment for [step 7](#7-optional-start-https-now).

## 4. Test it from your terminal

Why: check both rules with `curl` before you open the browser.

```console
laptop$ curl -s http://$IP/api/health; echo; curl -s http://$IP/ | grep -o '<title>.*</title>'
```

You should see the API answer through `/api` and the game page through `/`:

```text
{"status":"ok","version":"dcb0790"}
<title>Bug Squash Arena</title>
```

## 5. Play

Why: this is the moment the cluster becomes a website.

On your laptop, open `http://<your IP>` (`http`, not `https`), sign up and squash some bugs. The
footer says **Web 0902b98** and **API dcb0790**. Send the address to your neighbour: it is on the
internet now.

## 6. Find yourself in the logs

Why: the backend must see every visitor's real IP, because its login rate limit counts attempts
per IP.

```console
laptop$ kubectl logs -l app=backend --since=10m | grep /api/auth
```

You should see your laptop's public IP, not Google's (trimmed):

```text
203.0.113.25 POST /api/auth/signup 201 …
```

Google's load balancer sits between you and the backend and writes your IP and its own address into
the `X-Forwarded-For` header. `TRUST_PROXY: "2"` in the ConfigMap tells the backend to trust exactly
those two hops. Without it every visitor would look like Google, and all of them would share one
login limit. With it, every visitor has a limit of their own: 500 attempts per 15 minutes, set by
`AUTH_RATE_LIMIT_MAX` (the default of 30 is too low for a class sharing one campus Wi-Fi IP).

## 7. (Optional) Start HTTPS now

Why: Google's certificate takes 15-60 minutes, so ask for it now and finish on page 10. You need a
domain you control (the course uses `k8s.gulfheight.com`). No domain? Skip this step.

In Cloudflare, *DNS → Records → Add record*: type `A`, name `k8s`, IPv4 address = your IP,
**Proxy status: DNS only** (grey cloud). Your own domain? Replace `k8s.gulfheight.com` in
`manifests/08-https.yaml` first. Then:

```console
laptop$ dig +short k8s.gulfheight.com @1.1.1.1
laptop$ kubectl apply -f manifests/08-https.yaml
```

You should see your IP, then the certificate request and the Ingress updated in place:

```text
136.81.240.49
managedcertificate.networking.gke.io/bugsquash-cert created
ingress.networking.k8s.io/bugsquash configured
```

The site keeps working on plain HTTP in the meantime.

## Checkpoint

- `kubectl get ingress bugsquash` shows your IP in `ADDRESS`.
- `http://<your IP>` serves the game, and `/api` reaches the backend.
- The backend logs your real public IP.

Next: ship a new version while people play. [8. Rolling updates](08-rolling-updates.md).

<details>
<summary>Going deeper</summary>

- **What Google built:** **Network services → Load balancing** shows the load balancer (its name
  starts with `k8s2-`): the front end on your IP, the two path rules and the backends.
- **Is every pod healthy for Google?** `kubectl describe ingress bugsquash` shows the annotation
  `ingress.kubernetes.io/backends` with `HEALTHY` or `UNHEALTHY` per backend.
- **Why the IP is global:** a GKE Ingress makes a global external Application Load Balancer.
  Visitors connect to the Google location closest to them, and Google's own network carries the
  request to Warsaw.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ADDRESS` still empty after 10 minutes | `kubectl describe ingress bugsquash` and read the events. `the given static IP name bugsquash-ip doesn't translate to an existing static IP`: reserve it as **Global** (step 1). |
| `404`, `502` or *Server Error* from Google | Still building: wait up to 10 minutes. Longer? All frontend and backend pods must be `1/1` in `kubectl get pods`. |
| `echo $IP` prints an empty line | New terminal window: set `IP` again (step 1). |
| `Too many attempts. The bugs need a break too…` | 500 sign-ups or logins per IP per 15 minutes were used up (a class on one Wi-Fi shares one IP): wait 15 minutes, or use your phone's data. |
| `dig` prints nothing, or not your IP | The record is missing, wrong, or proxied (orange cloud): set it to **DNS only**. No `dig`? `nslookup k8s.gulfheight.com 1.1.1.1`. |
