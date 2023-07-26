import ParsonsBlock from "./parsonsBlock";

export default class SettledBlock extends ParsonsBlock {
    constructor(problem, lines) {
        // problem: Parsons instance
        // lines: lines inside the block
        super(problem, lines);

        this.isSettled = true;
        // add a css class
        $(this.view).addClass("settled-block");
        $(this.view).addClass("disabled");
    }
}