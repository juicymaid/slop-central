<template>
	<div class="flex flex-wrap gap-2">
		<span
			v-for="(tag, i) in tags"
			:key="i"
			class="inline-flex items-center rounded-full px-2.5 py-1 text-sm cursor-move select-none border bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-200 dark:border-slate-600 dark:hover:bg-slate-600"
			draggable="true"
			@dragstart="onDragStart(i, $event)"
			@dragover.prevent
			@drop="onDrop(i)"
			@dragend="onDragEnd"
		>
			{{ tag }}
			<button
				type="button"
				class="ml-2 text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400"
				@click="removeTag(i)"
				aria-label="Remove"
				title="Remove"
			>×</button>
		</span>
	</div>
</template>

<script setup>
//props
import { defineProps, defineEmits, ref, watch } from 'vue';
const props = defineProps({
	prompt: {
		type: String,
		required: true
	}
});
const emit = defineEmits(['update:prompt', 'change', 'prompt-changed']);

const parsePrompt = (str) =>
	!str ? [] : str.split(',').map(s => s.trim()).filter(Boolean);
const toPromptString = (list) => list.join(', ');

const tags = ref(parsePrompt(props.prompt));

// prevent duplicate emits when we update locally then receive the prop back
const isInternalUpdate = ref(false);

watch(() => props.prompt, (val) => {
	if (isInternalUpdate.value) {
		isInternalUpdate.value = false;
		tags.value = parsePrompt(val);
		return;
	}
	tags.value = parsePrompt(val);
	emit('prompt-changed', { value: val ?? '', tags: [...tags.value], source: 'external' });
});

const update = (reason, detail = {}) => {
	const value = toPromptString(tags.value);
	isInternalUpdate.value = true;
	emit('update:prompt', value);
	emit('change', [...tags.value]);
	emit('prompt-changed', { value, tags: [...tags.value], source: 'user', reason, ...detail });
};

const removeTag = (i) => {
	tags.value.splice(i, 1);
	update('remove', { index: i });
};

const draggingIndex = ref(null);

const onDragStart = (i, e) => {
	draggingIndex.value = i;
	e.dataTransfer && e.dataTransfer.setData('text/plain', String(i));
	if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move';
};
const onDrop = (i) => {
	const from = draggingIndex.value;
	if (from === null || from === i) return;
	const [item] = tags.value.splice(from, 1);
	tags.value.splice(i, 0, item);
	draggingIndex.value = null;
	update('reorder', { from, to: i, moved: item });
};
const onDragEnd = () => {
	draggingIndex.value = null;
};
</script>

<!-- Removed <style scoped> in favor of Tailwind classes -->