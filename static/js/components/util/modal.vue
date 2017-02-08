<template>
  <div class="vueModal">
    <div class="modal" tabindex="-1" v-bind:class="{ in: open }" v-bind:style="modalStyle">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            {{ header }}
          </div>
          <div class="modal-body">
            <slot></slot>
          </div>
          <div class="modal-footer">
            <a class="btn btn-default" v-on:click="close">Cancel</a>
            <a class="btn btn-primary" v-on:click="submit">Accept</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['show', 'header'],
  data: function(){
    return {
      open: this.show
    };
  },
  methods: {
    close: function(){
      this.open = false;
      this.$emit('close');
    },
    submit: function(){
      this.open = false;
      this.$emit('submit');
    }
  },
  watch: {
    show: function(value){
      this.open = value;
    }
  },
  computed: {
    modalStyle: function(){
      return this.open ? { 'padding-left': '0px;', display: 'block' } : {};
    }
  }
};
</script>
