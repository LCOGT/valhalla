<template>
<div class="row">
  <div class="col-md-12">
    <h1>Planning Tools</h1>
    <h3>Network Contention</h3>
    <Contention></Contention>
  </div>
</div>
</template>
<script>
import Contention from './components/contention.vue';

export default {
  name: 'tools',
  components: {Contention},
};
</script>
<style>
</style>
