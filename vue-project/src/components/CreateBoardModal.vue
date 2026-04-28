<template>
  <div class="fixed inset-0 flex items-center justify-center z-50">
    <!-- Modal overlay -->
    <div class="absolute inset-0 bg-[#0D0D12]/80 backdrop-blur-sm" @click="$emit('close')"></div>
    <!-- Modal content -->
    <div class="relative bg-[#1A1A24] rounded-[2rem] shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-[#2A2A35] w-11/12 max-w-md p-8">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-xl font-bold text-[#FAF8F5] tracking-tight">Create Board</h2>
        <button class="text-[#FAF8F5]/50 hover:text-[#FAF8F5] transition-colors" @click="$emit('close')">
          <!-- close icon -->
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="mb-6">
        <input type="text" placeholder="Board Name" class="w-full p-4 bg-[#0D0D12] text-[#FAF8F5] placeholder-[#FAF8F5]/40 border border-[#2A2A35] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#C9A84C] focus:border-[#C9A84C] transition-colors font-mono text-sm" v-model="boardName">
      </div>
      <div class="flex justify-end">
        <button class="magnetic-button bg-[#C9A84C] text-[#0D0D12] px-6 py-3 rounded-xl hover:bg-[#B89A45] font-semibold transition-all duration-300" @click="createBoard">Create</button>
      </div>
    </div>
  </div>
</template>

<script>
import { PostToApi } from '@/api';

export default {
  name: "CreateBoardModal",
  data() {
    return {
      boardName: ""
    };
  },
  methods: {
    async createBoard() {
        await PostToApi('board', { name: this.boardName });
        //refresh page
        window.location.reload();
    }
  }
};
</script>

<style scoped>
/* ...existing code... */
</style>