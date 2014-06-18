Feature: Error fixing
    In order to  fix errors
    As an author
    I will edit my journal entries

    Scenario: Title Misspelling
        Given my post title is misspelled 'cris'
        When I edit it 'Chris'
        Then it will be spelled correctly 'Chris'
