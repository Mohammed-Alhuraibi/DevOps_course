# Stage 4: Services

[Kubernetes lesson](../README.md) · [Concepts](../concepts.md) · [← Stage 3](stage-3-deployments.md) · **Stage 4** · [Stage 5 →](stage-5-configmaps-and-secrets.md)

Pods come and go, and every new one gets a new name and a new IP address. Nobody can keep a phone
book of them. A Service is one stable name in front of all of them: call `frontend`, and one of the
ready frontend pods answers.

**By the end:** you call the frontend by name from inside the cluster and prove that the calls are
spread over all three pods.

![Services: the Ingress for /api and any pod calling http://backend:3000 reach the Service backend, which selects the pods labelled app=backend and spreads the calls over them; a replaced pod gets a new IP but the Service name stays, like a company phone number that any free agent answers; inside the cluster DNS turns the name backend into the Service's fixed IP](../images/slides/k8s-05-services.svg)

## 1. Create the Service

Why: the Service finds its pods by the label `app=frontend`, the one in the Deployment's template.

```console
laptop$ kubectl apply -f manifests/03-frontend-service.yaml
laptop$ kubectl get service frontend
```

You should see a fixed `CLUSTER-IP`, reachable only inside the cluster (`EXTERNAL-IP` is `<none>`):

```text
service/frontend created
NAME       TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
frontend   ClusterIP   34.118.226.213   <none>        8080/TCP   0s
```

## 2. See who is behind it

Why: Kubernetes keeps a live list of the ready pods behind every Service.

```console
laptop$ kubectl get endpointslices -l kubernetes.io/service-name=frontend
```

You should see three pod IPs, the same as in the `IP` column of `kubectl get pods -o wide`:

```text
NAME             ADDRESSTYPE   PORTS   ENDPOINTS                       AGE
frontend-9zh5r   IPv4          8080    10.76.2.9,10.76.1.8,10.76.0.9   1s
```

Delete a pod and this list changes within seconds. The Service's name and IP never do.

**Look in the console:** **Kubernetes Engine → Gateways, Services & Ingress → Services** lists
`frontend` as a *Cluster IP* service; click it to see the pods behind it.

## 3. Start a toolbox pod

Why: Service names work only inside the cluster, so you need a pod to call from. This one has
`curl` and sleeps for a day, waiting for your commands; later pages use it too.

```console
laptop$ kubectl run toolbox --image=curlimages/curl:8.23.0 --restart=Never --command -- sleep 86400
laptop$ kubectl wait --for=condition=Ready pod/toolbox --timeout=60s
```

You should see:

```text
pod/toolbox created
pod/toolbox condition met
```

`kubectl run` creates a lone pod without a file: fine for a tool, never for the app.

## 4. Call the Service by name

Why: inside the cluster, DNS turns the name `frontend` into the Service's IP.

```console
laptop$ kubectl exec toolbox -- curl -s http://frontend:8080/healthz
```

You should see: `ok`.

> [!WARNING]
> On a brand-new cluster the DNS pods may still be starting (Stage 1), and this prints nothing at
> all. Wait a minute and run it again. It happened in our run too.

## 5. Prove the load balancing

Why: one name, three pods. Are the calls really spread?

```console
laptop$ kubectl exec toolbox -- sh -c 'for i in $(seq 1 9); do curl -s -o /dev/null http://frontend:8080/; done'
laptop$ kubectl logs -l app=frontend --prefix --since=30s | grep 'GET / ' | awk '{print $1}' | sort | uniq -c
```

The first line sends 9 requests to the Service. The second reads the last 30 seconds of logs of
every frontend pod (`--prefix` puts the pod's name in front of each line), keeps the `GET /` lines
and counts them per pod.

You should see all three pods (your numbers will differ):

```text
      2 [pod/frontend-d6d8d8454-n48vx/frontend]
      2 [pod/frontend-d6d8d8454-w85qg/frontend]
      5 [pod/frontend-d6d8d8454-zvd9c/frontend]
```

The Service picks a pod at random for every new connection, so a perfect 3/3/3 is rare. Over many
requests it evens out.

> [!NOTE]
> **A company phone number.** You call one number and any free agent answers. Agents change shifts;
> the number never changes. The pods are the agents, the Service is the number.

## Checkpoint

- A Service is a fixed name and IP in front of every ready pod with its label.
- Inside the cluster you call `http://frontend:8080`; you never type a pod IP.
- The `toolbox` pod stays running for later pages.

Next: the backend needs settings and passwords. [Stage 5: ConfigMaps and Secrets](stage-5-configmaps-and-secrets.md).

<details>
<summary>Going deeper</summary>

- **Service types.** `ClusterIP` (the default: inside the cluster only), `NodePort` (a port on every
  node) and `LoadBalancer` (one cloud load balancer per Service). We use `ClusterIP` plus one
  Ingress for the whole site (Stage 7).
- **The full name** is `frontend.bugsquash.svc.cluster.local`. Inside the same namespace the short
  name `frontend` is enough.
- **`34.118.226.213` looks public**, but it is GKE's internal range for Services; the internet can't
  reach it.
- **The `cloud.google.com/neg` annotation** in the file is GKE-only: it lets Google's load balancer
  (Stage 7) send requests straight to the pod IPs.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `curl` prints nothing | DNS is still starting on a new cluster: wait a minute, retry. Without `-s` curl shows the reason (`Could not resolve host: frontend`). |
| `pods "toolbox" already exists` | It is already running: just use it. |
| `error: unable to upgrade connection: container not found` | The toolbox is still starting: run the `kubectl wait` line again. |
| `ENDPOINTS` shows `<none>` | No ready pod has the label: `kubectl get pods -l app=frontend` must list three `1/1` pods. |
| One pod is missing from the count | It got no request this time: send the 9 requests again and use `--since=60s`. |
