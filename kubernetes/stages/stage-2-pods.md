# Stage 2: Pods

[Kubernetes lesson](../README.md) · [Concepts](../concepts.md) · [← Stage 1](stage-1-explore-the-cluster.md) · **Stage 2** · [Stage 3 →](stage-3-deployments.md)

In the Docker lesson you started containers with `docker run`. Kubernetes never runs a bare
container: it wraps it in a *pod*, gives the pod its own IP address and chooses a node for it. You
start one, look inside, open it in your browser, then delete it and watch what Kubernetes does about
that: nothing.

**By the end:** you have run the Bug Squash frontend as a pod, seen it in your browser, and know why
a lone pod is not enough.

![Pods: a pod is the shell around one container, like a pea pod around its pea, with an optional helper container and its own IP address; 01-pod.yaml shows the four parts of every Kubernetes file: apiVersion and kind say what it is, metadata gives the name hello-frontend and the label app: hello, spec says what you want, the frontend image sha-0902b98 on port 8080; kubectl delete pod hello-frontend removes it for good, because a lone pod is never brought back](../images/slides/k8s-03-pods.svg)

## 1. Read the file

Why: every Kubernetes file has the same four parts. Read this one and you can read them all.

```console
laptop$ grep -v '^#' manifests/01-pod.yaml
```

You should see the file without its header comment:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-frontend
  labels:
    app: hello            # a label is a sticky note; Services find pods by label
spec:
  containers:
    - name: frontend
      image: alhuraibisaeed/bugsquash-frontend:sha-0902b98   # the same image Docker ran
      ports:
        - containerPort: 8080
```

`apiVersion` and `kind` say *what* it is, `metadata` gives its name and labels, `spec` says what you
*want*: one container from the frontend image of the Docker stages, listening on port 8080.

## 2. Start the pod

Why: `apply` sends the file to the API server, the scheduler picks a node, and that node's kubelet
starts the container.

```console
laptop$ kubectl apply -f manifests/01-pod.yaml
laptop$ kubectl wait --for=condition=Ready pod/hello-frontend --timeout=120s
laptop$ kubectl get pods -o wide
```

You should see (trimmed; `-o wide` adds the IP and the node):

```text
pod/hello-frontend created
pod/hello-frontend condition met
NAME             READY   STATUS    RESTARTS   AGE   IP          NODE
hello-frontend   1/1     Running   0          7s    10.76.1.7   gke-bugsquash-default-pool-7204075e-xh1n
```

## 3. Read its story

Why: when a pod misbehaves, the events at the end of `describe` are the first place to look.

```console
laptop$ kubectl describe pod hello-frontend | sed -n '/^Events:/,$p'
```

You should see the scheduler choose a node, then the kubelet pull and start the image (trimmed;
the `sed` prints only from the `Events:` line on):

```text
  Type    Reason     Age   From               Message
  Normal  Scheduled  8s    default-scheduler  Successfully assigned bugsquash/hello-frontend to gke-bugsquash-default-pool-7204075e-xh1n
  Normal  Pulling    7s    kubelet            spec.containers{frontend}: Pulling image "alhuraibisaeed/bugsquash-frontend:sha-0902b98"
  Normal  Pulled     2s    kubelet            spec.containers{frontend}: Successfully pulled image … in 5.776s …
  Normal  Created    2s    kubelet            spec.containers{frontend}: Container created
  Normal  Started    2s    kubelet            spec.containers{frontend}: Container started
```

## 4. Logs and a look inside

Why: the same two habits as `docker logs` and `docker exec`, now through the cluster.

```console
laptop$ kubectl logs hello-frontend | tail -3
laptop$ kubectl exec hello-frontend -- sh -c 'hostname; id; cat /etc/os-release | head -1'
```

You should see nginx's last start-up lines, then the pod's name as its hostname and a non-root user:

```text
2026/11/10 12:16:27 [notice] 1#1: start worker processes
…
hello-frontend
uid=101(nginx) gid=101(nginx) groups=101(nginx)
NAME="Alpine Linux"
```

`uid=101` is the non-root user built into the image in the Docker stages: Kubernetes runs your image
exactly as it was built. `--` separates kubectl's own options from the command to run inside.

## 5. See it in your browser

Why: the pod's IP works only inside the cluster. `port-forward` opens a private tunnel from port
8080 on your laptop to port 8080 of the pod.

```console
laptop$ kubectl port-forward pod/hello-frontend 8080:8080
```

You should see the tunnel open; the command keeps running:

```text
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
```

Now open <http://localhost:8080> in your browser: the Bug Squash home page, served by the pod in
Warsaw. The terminal prints `Handling connection for 8080` for each request. The footer says
**Web 0902b98** and **API unreachable**: no backend yet (Stage 6). Press **Ctrl+C** in the terminal
to close the tunnel.

## 6. Delete it

Why: to see what Kubernetes does when a pod disappears.

```console
laptop$ kubectl delete pod hello-frontend
laptop$ kubectl get pods
```

You should see:

```text
pod "hello-frontend" deleted from bugsquash namespace
No resources found in bugsquash namespace.
```

Gone for good: nobody was watching over this pod, so nobody brought it back (on a crashed node it
would be lost the same way). Watching over pods is the job of the next page.

> [!NOTE]
> **A pea pod.** The container is the pea, the pod is the shell around it. Usually there is one pea
> per pod. Containers in one pod share its IP address, so a small helper, such as a log shipper,
> can sit right next to the app.

## Checkpoint

- A pod is one or more containers with one IP address, placed on a node by the scheduler.
- `get -o wide`, `describe`, `logs`, `exec` and `port-forward` are your five everyday tools.
- A deleted pod is never replaced.

Next: let Kubernetes keep pods alive for you. [Stage 3: Deployments](stage-3-deployments.md).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `STATUS` is `ErrImagePull` or `ImagePullBackOff` | The image name or tag is wrong: compare it with the file. `describe` (step 3) shows the exact error. |
| `STATUS` stays `Pending` | No node can take it yet: the events in `describe` say why. On a new cluster, wait a minute. |
| The browser can't reach `localhost:8080` | The tunnel isn't running: start `kubectl port-forward` again and leave that terminal open. |
| `unable to listen on any of the requested ports` | Another program holds port 8080: stop it, or use `8081:8080` and open <http://localhost:8081>. |
