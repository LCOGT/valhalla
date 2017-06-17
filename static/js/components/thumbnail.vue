<template>
  <div class="thumbnail-container">
    <span class="error" v-if="error"></span>
    <i class="fa fa-spinner fa-spin" v-show="!src && !error"></i>
    <a :href="largeUrl" v-show="src" title="View high resolution" target="_blank"><img class="thumbnail img-responsive" :src="src"></a>
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
    },
    largeUrl: function(){
      if(this.frame){
        return 'https://thumbnails.lco.global/' + this.frame.id + '/?width=4000&height=4000&image=true';
      }else{
        return '';
      }
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
