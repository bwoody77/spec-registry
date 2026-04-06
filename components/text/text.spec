component Text(content: string, variant: string = "body-md", selectable: boolean = true) {
  block {
    visibility: variant == "heading-xl"
    text(content) {
      style: type.heading-xl
      color: semantic.text-primary
    }
  }
  block {
    visibility: variant == "heading-lg"
    text(content) {
      style: type.heading-lg
      color: semantic.text-primary
    }
  }
  block {
    visibility: variant == "heading-md"
    text(content) {
      style: type.heading-md
      color: semantic.text-primary
    }
  }
  block {
    visibility: variant == "heading-sm"
    text(content) {
      style: type.heading-sm
      color: semantic.text-primary
    }
  }
  block {
    visibility: variant == "body-lg"
    text(content) {
      style: type.body-lg
      color: semantic.text-secondary
    }
  }
  block {
    visibility: variant == "body-md"
    text(content) {
      style: type.body-md
      color: semantic.text-secondary
    }
  }
  block {
    visibility: variant == "body-sm"
    text(content) {
      style: type.body-sm
      color: semantic.text-secondary
    }
  }
  block {
    visibility: variant == "label-sm"
    text(content) {
      style: type.label-sm
      color: semantic.text-primary
    }
  }
  block {
    visibility: variant == "caption"
    text(content) {
      style: type.caption
      color: semantic.text-tertiary
    }
  }
}
