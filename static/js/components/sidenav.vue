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
<style>
/* sidebar */
.bs-docs-sidebar {
    margin-top: 20px;
    margin-bottom: 20px;
    position: fixed;
}

/* all links */
.bs-docs-sidebar .nav>li>a {
    color: #999;
    border-left: 2px solid transparent;
    padding: 4px 20px;
    font-size: 16px;
    font-weight: 400;
}

/* nested links */
.bs-docs-sidebar .nav .nav>li>a {
    padding-top: 1px;
    padding-bottom: 1px;
    padding-left: 30px;
    font-size: 14px;
}

/* active & hover links */
.bs-docs-sidebar .nav>.active>a,
.bs-docs-sidebar .nav>li>a:hover,
.bs-docs-sidebar .nav>li>a:focus {
    color: #009ec3;
    text-decoration: none;
    background-color: transparent;
    border-left-color: #31b0d5;
}
/* all active links */
.bs-docs-sidebar .nav>.active>a,
.bs-docs-sidebar .nav>.active:hover>a,
.bs-docs-sidebar .nav>.active:focus>a {
    font-weight: 700;
}
/* nested active links */
.bs-docs-sidebar .nav .nav>.active>a,
.bs-docs-sidebar .nav .nav>.active:hover>a,
.bs-docs-sidebar .nav .nav>.active:focus>a {
    font-weight: 500;
}

/* hide inactive nested list */
.bs-docs-sidebar .nav ul.nav {
    display: none;
}
/* show active nested list */
.bs-docs-sidebar .nav>.active>ul.nav {
    display: block;
}
</style>
