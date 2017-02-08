<template>
  <span>
    <div class="form-group" :class="{ 'has-error': errors }" v-show="$parent.show">
      <label :for="field" class="col-sm-4 control-label">{{ label }}</label>
      <div class="col-sm-8">
        <select :id="field" v-bind:value="value" v-on:change="update($event.target.value)"
                :name="field" class="form-control">
          <option v-for="option in options" :value="option.value"
                  :selected="isSelected(option.value)" v-html="option.text"></option>
        </select>
        <span class="help-block text-danger" v-for="error in errors">{{ error }}</span>
      </div>
    </div>
    <div class="collapse-inline" v-show="!$parent.show">
      {{ label }}: <strong>{{ value || '...' }}</strong>
    </div>
  </span>
</template>
<script>
  export default {
    props: ['value', 'label', 'field', 'options', 'errors'],
    methods: {
      update: function(value){
        this.$emit('input', value);
      },
      isSelected: function(option){
        return option === this.value;
      }
    },
  };
</script>
