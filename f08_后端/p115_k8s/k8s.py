''' k8s
1 镜像工具
2 监控 + 自动重启 + 自动扩容
3 集群部署
'''

''' 
命令 -> 管理主机 -> 工作主机 -> pod -> 后端程序

'''


'''下载kind 
用daocker来模拟一个主机 从而模拟构建一个k8s集群 不会用于生产环境

在linux系统中安装kind 
1 下载kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
2 赋予执行权限
chmod +x ./kind
3 将kind移动到bin目录
sudo mv ./kind /usr/local/bin/kind
4 验证安装
kind version

'''

''' 
在k8s上 任何操作都等同一个yaml文件

1 创建集群
kind create cluster --config a1_kind.yaml
创建完成后会在docker中运行相应数量的镜像

2 为控制节点添加标签 ingress-ready=true 
kubectl label nodes aaa-control-plane ingress-ready=true

3 通过标签 将ingress-controller 部署到控制节点 从而可以从外网访问控制节点
kubectl apply -f a2_ingress-controller.yaml

4 查看ingress-controller 是否部署成功
kubectl get pods -n ingress-nginx

5 将docker镜像 导入到多个主机中
kind load docker-image dfastapi:v1.0.0 --name aaa

6 在主机中部署 pod
kubectl apply -f a3_k8s-pod.yaml

7 k8s 查看子pod 部署状态 ip 和 name
kubectl get pod -o wide

8 创建service 固定ip 和 负载均衡
kubectl apply -f a4_services.yaml

9 查看service
kubectl get svc

10 创建ingress 将service 暴露给外网
kubectl apply -f a5_ingress-nginx.yaml

11 查看ingress
kubectl get ingress


12 删除pod
kubectl delete pod 名称

13 删除集群
kind delete cluster --name aaa

'''

