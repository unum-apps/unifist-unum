k8s_yaml(kustomize('kubernetes/tilt'))

k8s_resource(
  objects=['unifist-unum:namespace'],
  new_name='namespace'
)

local_resource(
    name='config', resource_deps=['namespace'],
    cmd='kubectx docker-desktop && kubectl -n unifist-unum create configmap config --from-file config/ --dry-run=client -o yaml | kubectl apply -f -'
)

local_resource(
    name='secret', resource_deps=['namespace'],
    cmd='kubectx docker-desktop && kubectl -n unifist-unum create secret generic secret --from-file secret/ --dry-run=client -o yaml | kubectl apply -f -'
)

# api

docker_build('unum-apps-unifist-unum-api', './api')
k8s_resource('api', port_forwards=['15465:80', '15433:5678'], resource_deps=['secret'])

# gui

docker_build('unum-apps-unifist-unum-gui', './gui')
k8s_resource('gui', port_forwards=['5465:80'], resource_deps=['api'])
