<template>
  <div class="alert alert-dismissiable" :class="alertclass" role="alert">
    <slot></slot>
    <button class="close" data-dismiss="alert"><i class="fa fa-times"></i></button>
  </div>
</template>

<script>
  export default {
    props: ['alertclass'],
  };
</script>
