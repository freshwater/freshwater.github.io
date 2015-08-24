if (typeof constructFlipbook === 'undefined') {
    futureProc = [];

    constructFlipbook = function( $, flipbook, flipbookParent, indexInParent ) {

        // alert('semiinner');
        // alert($('.flipbookLink[name="' + flipbook.attr('name') + '"]').length);


        // this flipbook has already been processed by a nested call
        if (flipbook.hasClass('live')) { return; }

        var lis = flipbook.children('li');

        var showButtons = flipbook.attr('show-buttons') === 'true';
        var default1 = flipbook.attr('default');

        var obj = (function() { // block
            var index = 0;

            var listeners = [];
            var register = function( f ) {
                listeners.push(f);
            }

            var hoverIndex = 0;
            var isHovering = false;

            var hover = function( i ) {
                isHovering = true;
                hoverIndex = i;
                update();

                if (flipbookParent !== undefined) {
                    flipbookParent.hover(indexInParent)
                }
            }

            var unhover = function() {
                isHovering = false;
                update();

                if (flipbookParent !== undefined) {
                    flipbookParent.unhover();
                }
            }

            var update = function( newIndex ) {
                if( newIndex !== undefined ) {
                    index = newIndex;

                    if (flipbookParent !== undefined) {
                        flipbookParent.update(indexInParent);
                    }
                }

                // take care of cycling
                index = (index + lis.length) % lis.length;

                if( isHovering ) {
                    i = hoverIndex; }
                else {
                    i = index; }

                // update LI display
                lis.css('display','none')
                   .eq(i)
                   .css('display','table-cell');

                // update listeners (tabs etc)
                $.each( listeners, function( i, f ) {
                    f(index, isHovering, hoverIndex);
                } );
            };

            return {
                back: function() { index -= 1; update(); },
                forward: function() { index += 1; update(); },
                update: update,
                register: register,
                getActiveIndex: function() { return index; },
                hover: hover,
                unhover: unhover
            };
        })();

        // handle nested flipbooks
        lis.map( function( index, b ) {
            var innerFlipbooks = $(b).find('.flipbook');
            innerFlipbooks.each( function() {
                constructFlipbook( $, $(this), obj, index );
            } );
        } );

        /* buttons */
        var buttonSetup = function() {
            var leftbutton = $(document.createElement('button'))
                .html('<').click( obj.back );
            var rightbutton = $(document.createElement('button'))
                .html('>').click( obj.forward );

            var buttonDiv = $(document.createElement('div'))
                .append(leftbutton)
                .append(rightbutton)
                .addClass('buttonDiv');

            buttonDiv.insertAfter(flipbook);

            return buttonDiv;
        }


        /* tabs */
        var tabSetup = function() {
            var constructTab = function( element, index ) {
                var tab =
                    element
                    .attr('title', lis.eq(index).find('h4').html())
                    .mouseenter( function(){
                        $(this).addClass('hovering');
                        obj.hover(index); } )
                    .mouseleave( function(){
                        $(this).removeClass('hovering');
                        obj.unhover(); } )
                    .click( function(){
                        obj.unhover();
                        obj.update(index); } );

                var handler = function( thenIndex, isHovering, hoveringIndex ) {
                    if( isHovering && hoveringIndex == index ) {
                        tab.addClass('hovering'); }
                    else {
                        tab.removeClass('hovering'); }

                    if( thenIndex == index ) {
                        tab.addClass('selected'); }
                    else {
                        tab.removeClass('selected'); }
                };

                obj.register(handler);

                return tab;
            }

            // create a tab for each LI page
            tabs = lis.map( function( index, b ) {
                var name = $(b).attr('name');
                if (name === undefined)
                { name = index + 1 }

                return constructTab(
                    $(document.createElement('span'))
                    .addClass('tab')
                    .html(name)
                    , index); 
            } ).get();

            // create a tab for flipbook links
            // format is <span class="flipbookLink" name="flipbookname" index="index"> stuff </span>
            var processAllTabs = function() {
                $('.flipbookLink[name="' + flipbook.attr('name') + '"]').map( function() {
                    constructTab($(this).addClass('liveLink'), + $(this).attr('index') - 1);
                } );
            };

            processAllTabs();
            setTimeout(function() { processAllTabs(); }, 2000);
            futureProc.push(processAllTabs);
            
            return $(document.createElement('div')).addClass('underDiv').append(tabs);
        };


        /* initialize */
        flipbook.css('display','table');
        flipbook.removeClass('static').addClass('live');
        buttonDiv = buttonSetup();
        table = tabSetup(buttonDiv);

        if (!showButtons) {
            buttonDiv.children().attr('style', 'visibility: hidden');
        }

        table.insertAfter(buttonDiv.children().last());

        if (default1 !== undefined)
        { obj.update(default1 - 1); }
        else
        { obj.update(0); }

        /* maximize all list item heights so buttons don't jump around
         * when shuffling through items of different sizes */
        var maxHeight = Math.max.apply( null,
                lis.map(function(){ return $(this).height(); }).get() );

        lis.each(function(){ $(this).height(maxHeight + 10); });
    }

    processFlipbooks = function() {
        $('.flipbook').each( function() {
            constructFlipbook( $, $(this) );
        } );

        for (var k in futureProc) {
            futureProc[k]();
        }
    };
}

