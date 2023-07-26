import ParsonsBlock from "./parsonsBlock";
import ParsonsLine from "./parsonsLine";

export default class PlaceholderBlock extends ParsonsBlock {
    constructor(problem, placeholderLines, placeholderSize) {
        // problem: Parsons instance
        // size: how many blocks it is holding

        // have to have at least one parsonslines, otherwise will be error in ParsonsBlock.
        super(problem, placeholderLines);
        this.placeholderLines = placeholderLines;

        // create a normal parsons block, but use css to control visibility of normal content
        $(this.view).addClass("placeholder-block");
        
        // create a new div displaying how many blocks are missing
        this.placeholderSize = placeholderSize;
        var content = document.createElement('div');
        $(content).addClass("placeholder-text");
        content.innerText = `${placeholderSize} blocks are missing here`;
        $(this.view).append(content);

        this.isPlaceholder = true;
    }
}