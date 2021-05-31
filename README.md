This is the result on my work for this tech test.

## Task
Convert the jupyter notebook into modular code that could be evaluated for one or more
rounds of golf data from Arccos.

## Logic behind the code
To make this jupyter notebook modular, I decided to transform into a tool, composed of subtools.
</br>At the highest level, the tool ToClippd takes the 3 files and the name of the source ("arccos") and return a Clippd Dataframe.
</br>If there is any problem with any of the files ( file does not exist, wrong type of file or other), a message will be printed and a None value will be returned.

I added the name of the source as an input in case some parts of the code could be reused with another external source. More on that below.

## Organization
ToClipp is composed of 4 sub tools. They are all independent of each other.
###ReadFile
Reads the 3 files + the name of the source. The results are stored as private variables.
</br>I added source as an input because I supposed the loading could change depending on the source (each could have specific files).
###AggregateData
Aggregate the 3 dataframes and returns the aggregated dataframe.
###DeriveInsights
Derive the insights from some basic information from the aggregated dataframe.
###MapToClippd
Transform the dataframe into a Clippd Dataframe.
<br/>I added the source as an input there supposing the mapping could change depending on the external source.

## Additional Note
I was running out of time, and for that reason I didn't do all tests to have a full coverage.
<br/> All the tests for ReadFile and AggregateData ae done though.

