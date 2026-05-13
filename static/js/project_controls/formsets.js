window.ProjectControlsFormsets = window.ProjectControlsFormsets || (() => {
    function applyBootstrapClasses(root) {
        root.querySelectorAll('input, select, textarea').forEach((el) => {
            if (el.type === 'checkbox') {
                el.classList.add('form-check-input');
                return;
            }
            if (el.tagName === 'SELECT') {
                el.classList.remove('form-control');
                el.classList.add('form-select', 'form-select-sm');
                return;
            }
            el.classList.add('form-control', 'form-control-sm');
        });
    }

    function bindAddButton(options) {
        const button = document.getElementById(options.buttonId);
        const tbody = document.getElementById(options.tbodyId);
        const template = document.getElementById(options.templateId);
        const totalInput = document.getElementById(`id_${options.prefix}-TOTAL_FORMS`);
        if (!button || !tbody || !template || !totalInput) return;

        button.addEventListener('click', () => {
            const index = parseInt(totalInput.value, 10);
            const html = template.innerHTML.replace(/__prefix__/g, index);
            tbody.insertAdjacentHTML('beforeend', html);
            totalInput.value = index + 1;

            const row = tbody.lastElementChild;
            row?.classList.remove('formset-row-deleted', 'table-danger');
            if (row) applyBootstrapClasses(row);
            if (typeof options.afterAdd === 'function') options.afterAdd(row);
        });
    }

    return { applyBootstrapClasses, bindAddButton };
})();
