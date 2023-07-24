import ParsonsLine from "./parsonsLine";

export default class PlaceholderLine extends ParsonsLine {
    constructor(problem) {
        super(problem, "placeholder", false);
        console.log("creating placeholder line");
        this.isPlaceholderLine = true;
        console.log("placeholderline's view", this.view);
    }
}