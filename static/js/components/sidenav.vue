<template>
  <nav class="bs-docs-sidebar">
    <ul id="sidebar" class="nav nav-stacked">
      <li><a href="#general">General Info</a></li>
      <li v-for="(request, index) in userrequest.requests">
        <a :href="'#request' + index">Request #{{ index + 1}}</a>
        <ul class="nav nav-stacked">
          <li>
            <a :href="'#target' + index">Target</a>
          </li>
          <li v-for="(molecule, molIndex) in request.molecules">
            <a :href="'#molecule' + index + molIndex"> Configutation #{{ molIndex + 1}}</a>
          </li>
          <li v-for="(window, winIndex) in request.windows">
            <a :href="'#window' + index + winIndex">Window #{{ winIndex + 1}}</a>
          </li>
          <li>
            <a :href="'#constraints' + index">Constraints</a>
          </li>
        </ul>
      </li>
    </ul>
  </nav>
</template>

<script>
  export default {
    props: ['userrequest'],
  };
</script>
