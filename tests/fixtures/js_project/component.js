/**
 * A simple UI component class.
 * 
 * The Modernizer agent should convert this to TypeScript with proper types.
 */

class Button {
    constructor(label, onClick, disabled) {
        this.label = label;
        this.onClick = onClick;
        this.disabled = disabled || false;
    }

    render() {
        const disabledAttr = this.disabled ? ' disabled' : '';
        return `<button${disabledAttr}>${this.label}</button>`;
    }

    click() {
        if (!this.disabled && this.onClick) {
            this.onClick();
        }
    }

    setLabel(newLabel) {
        this.label = newLabel;
    }

    setDisabled(isDisabled) {
        this.disabled = isDisabled;
    }
}

class TextField {
    constructor(placeholder, value, onChange) {
        this.placeholder = placeholder;
        this.value = value || '';
        this.onChange = onChange;
    }

    render() {
        return `<input type="text" placeholder="${this.placeholder}" value="${this.value}" />`;
    }

    setValue(newValue) {
        const oldValue = this.value;
        this.value = newValue;
        if (this.onChange && oldValue !== newValue) {
            this.onChange(newValue, oldValue);
        }
    }

    clear() {
        this.setValue('');
    }
}

class Form {
    constructor(fields, onSubmit) {
        this.fields = fields || [];
        this.onSubmit = onSubmit;
    }

    addField(field) {
        this.fields.push(field);
    }

    render() {
        const fieldHtml = this.fields.map(f => f.render()).join('\n');
        return `<form>\n${fieldHtml}\n<button type="submit">Submit</button>\n</form>`;
    }

    submit() {
        const data = {};
        this.fields.forEach((field, index) => {
            data[`field_${index}`] = field.value;
        });
        if (this.onSubmit) {
            this.onSubmit(data);
        }
        return data;
    }
}

module.exports = { Button, TextField, Form };
