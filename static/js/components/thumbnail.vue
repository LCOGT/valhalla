<template>
  <div class="thumbnail-container">
    <span class="error" v-if="error"></span>
    <i class="fa fa-spinner fa-spin" v-show="!src && !error"></i>
    <img class="thumbnail img-responsive" :src="src" v-show="src">
  </div>
</template>
<script>
import $ from 'jquery';
export default {
  props: {
    frame: {},
    width: {
      default: 200
    },
    height: {
      default: 200
    }
  },
  data: function(){
    return {src: '', error: null};
  },
  watch: {
    frame: function(){
      this.src = '';
      this.fetch();
    }
  },
  computed: {
    url: function(){
      return 'https://thumbnails.lco.global/' + this.frame.id + '/?width=' + this.width + '&height=' + this.height + '&label=' + this.frame.filename;
    }
  },
  methods: {
    fetch: function(){
      var that = this;
      $.getJSON(this.url, function(data){
        that.src = data.url;
      }).fail(function(){
        that.error = 'Could not load thumbnail for this image';
      });
    }
  }
};
</script>
