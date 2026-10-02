# Apple container 实验：从 Mac 上的容器走到 Kubernetes

本路线覆盖正文全部 43 章：第 1–7 章先在 Apple container 中操作；后续章节复用这里构建的 OCI 镜像，在真实 Kubernetes 集群继续实验。每章的「Apple container 实验体验」给出任务、命令、验收和环境要求。网页版附录 E 完整收录本指南，单独保存 index.html 也能离线阅读。

建议小白分三轮：第一轮完成 E00–E03，能构建、访问、停止和启动网站；第二轮完成 E04–E07，理解网络、持久化、配置和排障；第三轮完成 E08，再按章进入 Kubernetes。安装、下载时间另计，前两轮约 60–90 分钟。

## E00 · 环境、版本与能力边界

核对日期：2026-10-02。原生命令基线为 **Apple container 1.0.0**，要求 **Apple silicon Mac、macOS 26 或更新版本**。本次实测环境为 macOS 27.0.1 / arm64 / container 1.0.0。不要用 Linux 或 Intel Mac 的操作结果推断本路线。[官方安装要求](https://github.com/apple/container/tree/1.0.0)。

Apple container 为每个 Linux 容器提供轻量虚拟机，Mac 主机运行 Darwin，容器内运行 Linux。OCI 镜像可复用，但仍要匹配节点架构；CLI 的名称相似不代表 Docker daemon、Compose、CRI 或 kind 驱动兼容。[官方技术说明](https://github.com/apple/container/blob/1.0.0/docs/technical-overview.md)。

| 你要学习的能力 | 实验环境 | 如何验收 |
|---|---|---|
| 镜像构建、进程、端口、挂载、配置、日志 | Apple container 原生 | E01–E07 的实际输出 |
| Pod、Deployment、Service、RBAC、调度 | Apple 构建镜像 + 独立 Kubernetes 集群 | E08 及对应章的 API 对象、Events、探针和恢复行为 |
| CNI、NetworkPolicy、CSI、HPA、网格、Operator | 具备相应组件的 Kubernetes 集群 | E09 的前置条件与本章实验 |
| 跨节点、HA、升级、节点扩容 | 专门的多节点实验集群 | 不能用几个独立 Apple 容器代表多个 Kubernetes 节点 |

从 [官方 Releases](https://github.com/apple/container/releases) 获取适合你系统的签名安装包，按官方说明安装。先检查版本，再查看该版本的命令帮助；本指南参考 [1.0.0 命令说明](https://github.com/apple/container/blob/1.0.0/docs/command-reference.md) 和 [官方入门实验](https://github.com/apple/container/blob/1.0.0/docs/tutorials/start-here.md)。

```bash
sw_vers
uname -m
container --version
container system start
container system status
container ls -a
```

预期：架构为 arm64，服务可用，能列出容器。首次启动可能提示下载 Linux 内核；按提示安装。若出现 XPC / apiserver 连接失败，先确认服务已启动，再检查终端的 macOS 权限与系统日志。

所有命令从本仓库根目录执行，使用 macOS 的终端。IP 提取步骤需要电脑上有 python3；也可以从 inspect 输出手动取 IP。名字以 lk8s-ac- 开头，使用本机 18080、18081、18082 端口；如名称或端口已被占用，先换名字/端口并同步后续命令，保留已有资源。

**版本提醒：**官方 main 分支已出现实验性的 `container k8s`，但 1.0.0 的发布文档与本机安装不包含该功能。它不是本指南的集群前提。以后若使用包含此功能的版本，先检查 `container k8s --help`，再按该版本的文档创建集群、加载镜像和处理 kubeconfig；主分支文档说明创建集群会写入默认 kubeconfig，不能假定配置完全隔离。[主分支实验功能](https://github.com/apple/container/blob/main/docs/command-reference.md)。

## E01 · 看见 Linux、进程和隔离（第 1、2、7 章）

```bash
container run --rm --name lk8s-ac-info docker.io/alpine:3.22 sh -c 'uname -a; id; ps; ls /proc/self/ns; cat /proc/self/cgroup; cat /sys/fs/cgroup/cgroup.controllers'
```

预期：显示 Linux / aarch64，能观察进程、namespace 入口和 cgroup v2 控制器。`--rm` 在退出后删除该容器。对比 Mac 上的 `uname -a`：为什么两个系统显示不同内核？

观察到 namespace 文件不等于证明两个 Apple 容器共享同一个 Linux 内核；不同 VM 内的 namespace inode 数字也不能直接比较。macOS 上不能直接照抄正文的 Linux 主机 nsenter、iptables、cgroup 路径。后续节点级实验需进入真正的 Linux Kubernetes 节点。

## E02 · 构建自己的网站镜像（第 3、5 章）

仓库已经提供 Dockerfile、网页与 .dockerignore。镜像基于 Python 3.13 Alpine，复制网页后用 UID/GID 1000 运行标准库 HTTP 服务；监听 0.0.0.0:8080。这是一份方便观察的教学网站，生产服务应另行选择合适服务器、镜像摘要和更新策略。

```bash
container build --platform linux/arm64 -t docker.io/learnk8s/apple-web:1.0 examples/apple-container
container image inspect docker.io/learnk8s/apple-web:1.0
container run -d --name lk8s-ac-web --cpus 1 --memory 256M -p 127.0.0.1:18080:8080 docker.io/learnk8s/apple-web:1.0
container ls
curl -f http://127.0.0.1:18080
```

预期：镜像架构为 arm64，容器正在运行，网页包含 `Hello Apple container!`。刚启动时请求可能连接失败，先用 logs 检查启动，再重试。`EXPOSE 8080` 只描述端口；真正发布到 Mac 的操作是 `-p`。

再执行相同 build，观察缓存；只修改网页后以新标签构建，观察 COPY 之后的步骤变化。相同标签可指向新内容，不意味着已经运行的容器或 Pod 自动更新。保留 1.0 标签用于后续实验。

本例 linux/arm64 镜像用于 Apple silicon 与 arm64 节点。amd64 集群要先使用支持的跨架构构建/执行方案生成对应镜像；Rosetta 或模拟运行并不改变现有镜像的平台字段。

## E03 · 生命周期与「谁负责恢复」（第 4、8、10–12 章）

先完成 E02。本例没有给网站添加 `--rm`，以便停止后重新启动。

```bash
container exec lk8s-ac-web id
container logs lk8s-ac-web
container stop lk8s-ac-web
container ls -a
container start lk8s-ac-web
curl -f http://127.0.0.1:18080
```

预期：网站以非 root 用户运行；stop 后为停止状态，start 后重新可访问。原生容器的停止与启动需你操作；E08 中 Deployment 的副本恢复由控制器完成。原生实验成功不能验收 Kubernetes 自愈、探针或调度。

自测：如果网站进程退出，谁观察期望状态并补副本？删除一个镜像、停止一个容器和删除一个 Pod 是同一件事吗？

## E04 · 网络、IP、端口与 DNS（第 6、13、15–20 章）

先完成 E02。创建专用网络及第二个网站，观察同网络通信。下面只从自己网站的 inspect 输出提取 IP，不写死文档中的示意地址。[官方网络与端口操作](https://github.com/apple/container/blob/1.0.0/docs/how-to.md)。

```bash
container network create lk8s-ac-net
container run -d --name lk8s-ac-netweb --network lk8s-ac-net --memory 256M docker.io/learnk8s/apple-web:1.0
container inspect lk8s-ac-netweb
WEB_IP=$(container inspect lk8s-ac-netweb | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["status"]["networks"][0]["ipv4Address"].split("/")[0])')
container run --rm --name lk8s-ac-client --network lk8s-ac-net docker.io/alpine:3.22 wget -T 5 -qO- "http://$WEB_IP:8080"
container run --rm --name lk8s-ac-dns --network lk8s-ac-net docker.io/alpine:3.22 sh -c 'cat /etc/resolv.conf; nslookup example.com'
```

预期：同网络 client 取得网页；resolv.conf 有解析配置，公网 DNS 查询成功需网络可用。上面的 IP 路径以本机 1.0.0 实际输出为准：status.networks[].ipv4Address；官方 how-to 中顶层 networks/address 的旧示例不可直接复制。网络名不是 Kubernetes Namespace，IP 不是 ClusterIP；端口发布不是 Service 负载均衡。

可选对比：去掉 client 的 `--network lk8s-ac-net`，使用另一个名字运行同一请求，观察默认网络到独立网络的请求超时。Apple 1.0.0 官方说明不同网络隔离；这不能替代 CNI 的 NetworkPolicy 规则验收。VPN、代理和 macOS 本地网络权限可能影响连接，排障时同时记录它们。

小白路线使用 IP 和 loopback 端口，不修改全局 DNS。官方教程的 `sudo container system dns create ...` 会配置 Mac 的 /etc/resolver；它是可选的主机域名功能，不能用来证明 CoreDNS、Service 域名或集群 DNS 配置正确。

## E05 · 挂载与数据是否真的留下（第 6、21–23 章）

先完成 E02。第一步将仓库网页目录只读挂载到 /site，镜像内容会被挂载覆盖；在 Mac 修改网页再刷新，无需重建镜像。

```bash
container run -d --name lk8s-ac-bind -p 127.0.0.1:18081:8080 -v "$(pwd)/examples/apple-container:/site:ro" docker.io/learnk8s/apple-web:1.0
curl -f http://127.0.0.1:18081
container volume create -s 64M lk8s-ac-data
container run --rm --name lk8s-ac-write -v lk8s-ac-data:/data docker.io/alpine:3.22 sh -c 'echo persisted > /data/message.txt'
container run --rm --name lk8s-ac-read -v lk8s-ac-data:/data docker.io/alpine:3.22 cat /data/message.txt
container volume inspect lk8s-ac-data
```

预期：第二个容器读到 persisted，说明数据位于独立卷中；没有使用卷的容器可写层不提供这项跨删除保留的约定。这里只串行挂载卷，避免把本地 ext4 卷误当作多写者共享文件系统。

Apple named volume 由本地容器平台管理；它没有 PVC 绑定、StorageClass 动态供给、CSI 或跨节点恢复语义。`--rm` 不等于删除持久卷；官方说明匿名卷也需单独清理。本路线用命名卷便于识别与清理。

自测：如果删除容器、卷、Mac 本地目录，分别会损失什么？持久化与备份有什么区别？

## E06 · 配置、权限与资源（第 24–31、37、38 章）

先完成 E02。使用明确的非敏感配置，观察 UID、Linux capability 状态和资源。网站仅进行读取，可运行于只读根文件系统。

```bash
container run -d --name lk8s-ac-secure --cpus 1 --memory 256M --read-only --cap-drop ALL -e LAB_MODE=apple -p 127.0.0.1:18082:8080 docker.io/learnk8s/apple-web:1.0
container exec lk8s-ac-secure sh -c 'id; echo "$LAB_MODE"; grep Cap /proc/self/status'
container inspect lk8s-ac-secure
container stats --no-stream lk8s-ac-secure
curl -f http://127.0.0.1:18082
```

预期：UID 1000，输出 apple，网站可访问，inspect 显示资源配置。capability 的值可与 E01 root 容器对照；不要只凭 UID 判断全部安全配置。

`--cpus 1` 配置 VM 的 vCPU，`--memory 256M` 配置容器 VM 的内存预算，不能直接等同于 Kubernetes 的 CPU 配额、requests、limits 或 QoS。stats 与 Mac 活动监视器口径不同，内核及 VM 有额外开销。通过负载和观察学习后，在 E08 集群里检查实际 requests/limits、调度与 OOM 事件。

这里的环境变量不是 ConfigMap/Secret；不要把真实凭据写进 Dockerfile、镜像层、网页或提交记录。原生用户权限也不是 RBAC、Pod Security Admission、ResourceQuota、PDB 或 HPA。

## E07 · 日志、性能与失败证据（第 32–34、39 章）

先完成 E02。给网站发请求，关联日志与资源；再访问不存在的页面，区分应用返回错误和网络连接失败。

```bash
curl -f http://127.0.0.1:18080
curl -i http://127.0.0.1:18080/missing
container logs lk8s-ac-web
container stats --no-stream lk8s-ac-web
container inspect lk8s-ac-web
```

预期：首页 200，不存在的页面 404，logs 可看到请求路径。stop 网站后再次访问，通常是连接失败，原因与 404 不同；用 E03 的 start 恢复。不要把一次 stats 快照当作容量基准或链路追踪结果。

| 现象 | 先读的证据 | 下一步 |
|---|---|---|
| 服务/XPC 不可用 | system status | 启动服务，再检查版本、权限和系统日志 |
| 拉取/构建失败 | 拉取或 build 输出 | 核对标签、网络、仓库认证与架构 |
| 网站连不上 | ls、logs、inspect | 确认进程、监听地址、端口发布和 Mac 权限 |
| 跨容器失败 | network inspect、容器 IP、resolv.conf | 确认同网络；区别 DNS 与 HTTP 失败 |
| 目录无内容/不可写 | 挂载参数、id、路径权限 | 挂载覆盖镜像目录；检查只读和 UID |
| Kubernetes 镜像找不到 | describe pod 的 Events | Apple 镜像仓库与节点仓库独立，回到 E08 导入 |

macOS 内核不是 Linux，不能在 Mac 上直接运行正文的 Linux bpftrace/cgroup/iptables 命令。Apple 容器的 Linux VM 与 Kubernetes 节点 VM 又是不同观测边界；集群 eBPF 工具需在支持相应内核、权限和组件的 Linux 节点运行。

## E08 · 同一镜像进入真正的 Kubernetes（第 7–14 章与后续实验）

### E08.1 · 准备独立集群

Apple container 1.0.0 不提供本路线的 Kubernetes 集群，也不是 minikube 的 docker 驱动。这里让 Apple container 负责镜像开发，minikube 的 QEMU Linux VM 负责 Kubernetes；两者可以同时运行，不需要 Docker daemon。

以下路线要求另外装好 minikube、kubectl、QEMU。若使用 Homebrew，可按需安装 `brew install minikube kubernetes-cli qemu`，然后查看官方 [QEMU 驱动](https://minikube.sigs.k8s.io/docs/drivers/qemu/) 文档。不要复用或重建已有业务集群。为这个新 profile 留出 2 核 / 4 GiB，并预留 Apple 网站与 BuildKit 的额外资源。

```bash
minikube start -p learnk8s-apple --driver=qemu --network=builtin --container-runtime=containerd --cpus=2 --memory=4096
kubectl --context=learnk8s-apple get nodes -o wide
kubectl --context=learnk8s-apple version
```

预期：arm64 Linux 节点 Ready，客户端版本符合服务端的版本差异策略。builtin 网络不支持 minikube service / tunnel；本路线使用 kubectl port-forward。Mac 上终端/IDE 的本地网络权限可能影响连接。无法创建集群时先解决驱动或下载问题，再继续导入。

若已有专门的学习集群，可使用它，但要在后续所有命令中明确替换 context，并按该集群流程导入镜像或使用你自己的镜像仓库。不能对远程集群照抄 minikube image load；不能把本地 arm64 镜像交给 amd64 节点。多节点离线导入需确保每个可调度节点都能找到对应镜像。

### E08.2 · 导出、导入与部署

先完成 E02。Apple 镜像存储与 Kubernetes 节点的 containerd 存储彼此独立。导出的是镜像归档，不是运行容器的 rootfs export；归档放在系统临时目录，不进 Git。minikube 官方支持从归档加载镜像。[镜像加载命令](https://minikube.sigs.k8s.io/docs/commands/image/)。

```bash
APPLE_IMAGE_ARCHIVE="${TMPDIR:-/tmp}/learnk8s-apple-web.tar"
container image save --platform linux/arm64 --output "$APPLE_IMAGE_ARCHIVE" docker.io/learnk8s/apple-web:1.0
minikube -p learnk8s-apple image load "$APPLE_IMAGE_ARCHIVE"
minikube -p learnk8s-apple image ls
kubectl --context=learnk8s-apple apply -f examples/apple-container/app.yaml
kubectl --context=learnk8s-apple -n apple-lab rollout status deployment/apple-web --timeout=180s
kubectl --context=learnk8s-apple -n apple-lab get deployment,replicaset,pods,service
```

预期：节点镜像列表有 docker.io/learnk8s/apple-web:1.0，Deployment 为 2/2。清单设 `imagePullPolicy: Never`，若未导入则报告 ErrImageNeverPull；它不会尝试从公共仓库拉取你未发布的镜像。镜像名称与标签必须完全一致。[Kubernetes 镜像规则](https://kubernetes.io/docs/concepts/containers/images/)。

完整清单含 Namespace、Deployment、Service、探针、资源限制及非 root 安全配置。网站直接读取镜像内网页，方便确认与 Apple 原生容器运行的是同一份应用；原来的 beginner/app.yaml 则保留 ConfigMap 网页实验，两份实验的命名空间不同。

### E08.3 · 访问、扩容、恢复

终端 A 保持运行：

```bash
kubectl --context=learnk8s-apple -n apple-lab port-forward service/apple-web 18083:80
```

终端 B：

```bash
curl -f http://127.0.0.1:18083
kubectl --context=learnk8s-apple -n apple-lab scale deployment/apple-web --replicas=3
kubectl --context=learnk8s-apple -n apple-lab rollout status deployment/apple-web --timeout=180s
kubectl --context=learnk8s-apple -n apple-lab get pods -l app=apple-web
```

预期：相同网页，三个 Ready Pod。选其中一个 Pod 的完整名字后删除它，观察 Deployment 补回。不要一次删除所有 Pod。port-forward 选定的 Pod 被删除时，转发可能断开，需重新启动；转发成功不等于 ClusterIP 负载均衡已验收。

```bash
# 将 POD_NAME 替换为上一步一个实际的 Pod 名
kubectl --context=learnk8s-apple -n apple-lab delete pod POD_NAME
kubectl --context=learnk8s-apple -n apple-lab get pods -l app=apple-web -w
```

Ctrl+C 结束观察。再 apply 原清单、等待 rollout，副本恢复为文件声明的 2。对照 E03：恢复发生在哪个系统、由哪个控制器完成？

若要验证集群内 DNS / Service 路径，在学习命名空间创建临时 client（需要节点能拉取 Alpine 镜像），执行内部 HTTP 请求后删除它：

```bash
kubectl --context=learnk8s-apple -n apple-lab run client --image=docker.io/alpine:3.22 --restart=Never --command -- sleep 3600
kubectl --context=learnk8s-apple -n apple-lab wait --for=condition=Ready pod/client --timeout=120s
kubectl --context=learnk8s-apple -n apple-lab exec client -- nslookup apple-web
kubectl --context=learnk8s-apple -n apple-lab exec client -- wget -T 5 -qO- http://apple-web
kubectl --context=learnk8s-apple -n apple-lab delete pod client
```

预期：Service 名可解析，HTTP 返回相同网页；结合 EndpointSlice 验证就绪后端。完整的负载均衡、NetworkPolicy 或 mesh 还要按对应章节分别验收。[Service 与 DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)。

## E09 · 全部章节的实验前提与深入路线

每章导读后均有 Apple 路线任务，先做对应的 E01–E08，再继续正文。下面是进入各篇时的环境检查；「能查询」与「功能正确工作」分开验收。

| 章节 | Apple 体验如何衔接 | 继续深入的必要条件 |
|---|---|---|
| 1–7 容器基础 | E01–E07 原生实验 + E08 镜像流转 | Linux 主机内核操作留到 Linux VM；不能照搬 Docker socket / Compose |
| 8–14 架构与工作负载 | 用 apple-web 观察副本、Pod、Service、标签 | E08 Ready 集群；保持明确 context / namespace |
| 15–20 网络 | 对比 E04 的 IP 与集群 Service / DNS | CNI 实现；Gateway/Ingress 控制器；策略实验须有支持 NetworkPolicy 的 CNI |
| 21–23 存储 | 对比 E05 的本地卷与 PVC / StorageClass | 可用的供给器；CSI 实验需真实 CSI driver；本地 hostPath 不能验收跨节点恢复 |
| 24–26 配置与安全 | 将 E06 的配置、非 root 和只读设置迁入 Pod | ConfigMap/Secret 清单、RBAC 权限及 PSA；不要使用真实凭据 |
| 27–31 调度与弹性 | 查看 apple-web 的 requests、limits 与分配节点 | 拓扑/反亲和/抢占需多节点与可控资源；HPA 需可用指标 API；PDB 不保证每次故障可用 |
| 32–34 可观测性 | 对比 E07 logs/stats 与集群日志和指标 | Metrics Server/监控/追踪组件；eBPF 需要 Linux 节点内核与权限 |
| 35–39 生产与排障 | 以同一镜像做变更、资源核对和故障记录 | HA/升级/容灾另建可销毁多节点环境；单节点练习不能验收生产可靠性 |
| 40–42 服务网格 | 以 apple-web 做业务端，执行本章流量实验 | 对应版本 Istio/CRD；sidecar 与 Ambient 分开选；arm64 镜像和节点内核要求均需核对 |
| 43 扩展 | 用 apple-web 理解控制器管理的对象 | 安装示例 CRD/Operator/webhook；apiextensions 与业务镜像构建是两个层次 |

配套完整清单：第 20 章 networkpolicy.yaml、第 21–22 章 storage.yaml、第 24 章 configmap.yaml、第 25 章 rbac.yaml、第 31 章 hpa.yaml、第 37 章 quota.yaml，均位于 examples/apple-container/。它们都以 E08 创建的 apple-lab 为前提，按章单独部署，避免一次开启互相影响的策略。storage.yaml 的教学写入使用 root；生产存储权限需按驱动设置 UID/GID/fsGroup。

第 19、20、22、23、31、34、40–43 章的插件实验，先完成该章已有的安装前提；不要将正文 YAML 合并片段当完整清单直接 apply。在 E08 的新集群，服务网格、eBPF、CSI 等尚未安装是正常情况。

已有 Docker/Compose 示例可以保留作为对照。只有具备相同能力且经核对的 build/run/exec/logs 等基础操作才迁到原生命令；Docker 网络驱动、docker.sock、docker compose、CRI 配置以及节点维护命令不能机械替换为 container。Apple VM 的边界仍要明确。

## E10 · 清理、复盘与实测记录

按你实际完成的步骤清理。本段名字均属于本路线；先查 ls，已不存在的资源不必重复删除。退出仍在运行的 port-forward / watch 后执行。

```bash
container stop lk8s-ac-web lk8s-ac-netweb lk8s-ac-bind lk8s-ac-secure
container delete lk8s-ac-web lk8s-ac-netweb lk8s-ac-bind lk8s-ac-secure
container network delete lk8s-ac-net
container volume delete lk8s-ac-data
container image delete docker.io/learnk8s/apple-web:1.0
```

上述 volume delete 会删除本实验的 persisted 数据，先确认已不需要。短时容器使用 --rm 自动删除。镜像归档可从系统临时目录按文件名删除。

逐章恢复：删除 apple-web-deny-ingress 恢复网络；删除 HPA 后再 apply app.yaml 恢复副本管理；删除 apple-quota 恢复准入；执行 `kubectl --context=learnk8s-apple -n apple-lab set env deployment/apple-web LAB_MODE-` 删除环境变量。想清理卷实验时先删 volume-writer，再删 apple-data PVC；PV 是否删除由回收策略决定，先检查再处理。

完成 Kubernetes 部分后，只清理实验命名空间；若整个专用 minikube profile 也不再需要，再删除它：

```bash
kubectl --context=learnk8s-apple delete namespace apple-lab
minikube delete -p learnk8s-apple
```

不要使用 --all / prune 清理其他项目，也不要在还有工作容器时停止全局服务或 BuildKit。只有确认服务完全空闲且希望退出平台时，才按官方说明停止服务。

复盘标准：能区分镜像仓库与节点仓库，说明 Apple VM 与 Kubernetes 节点的边界；能独立访问网页、读取日志、保存与清理卷；进入集群后能解释控制器补副本、Service/DNS、资源和插件的前提。

**验证范围：**本次已经实际运行 Apple container 的容器/镜像构建、网站访问、生命周期、专用网络通信与隔离、DNS、挂载、持久卷、非 root/只读/capability、资源统计、日志及镜像归档实验。新增 Kubernetes 清单已做 YAML 和官方 OpenAPI 静态检查；本机没有可用的 QEMU Kubernetes 集群，镜像导入、Pod 运行与各插件实验仍需在上述集群环境中验收，不能视为已实测。
